import re
import logging
from typing import List, Dict, Any, Optional
from app.models.schemas import ToolCallDetail, ChatResponse
from app.tools.registry import tool_registry

logger = logging.getLogger("jarvis.planner")


class ExecutionStep:
    def __init__(self, step_number: int, instruction: str, tool_name: Optional[str] = None, arguments: Optional[Dict[str, Any]] = None, depends_on_previous: bool = False):
        self.step_number = step_number
        self.instruction = instruction
        self.tool_name = tool_name
        self.arguments = arguments or {}
        self.depends_on_previous = depends_on_previous
        self.executed = False
        self.success = False
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None


class MultiStepPlanner:
    """
    Structured Sequential Task Planner for multi-command user directives.
    Breaks down compound commands into discrete verifiable steps, executes them in safe order,
    and reports per-step verification.
    """

    ACTION_VERBS = [
        "open", "launch", "play", "send", "turn", "set", "minimize", "maximize",
        "find", "search", "create", "delete", "close", "mute", "unmute",
        "go to", "navigate to", "navigate", "lock", "kill", "restore", "run", "start", "visit"
    ]

    SPLIT_PATTERN = re.compile(
        r'(?:,\s*and\s+then\s+|,\s*then\s+|\s+and\s+then\s+|,\s*and\s+|;\s*|,\s*|\s+then\s+|\s+and\s+(?='
        + '|'.join(v.replace(' ', r'\s+') for v in ACTION_VERBS)
        + r'\b))',
        re.IGNORECASE
    )

    @classmethod
    def is_compound_directive(cls, text: str) -> bool:
        """Determine if a prompt contains multiple sequential actions."""
        if not text:
            return False
        clean = text.strip()
        lower = clean.lower()

        # Single-intent music or video playback should NOT be split into compound steps
        if ("spotify" in lower and any(w in lower for w in ["play", "listen", "stream", "track", "song"])) or \
           ("youtube" in lower and any(w in lower for w in ["play", "watch", "stream", "song", "video"])):
            parts = [p.strip() for p in cls.SPLIT_PATTERN.split(clean) if p.strip()]
            if len(parts) < 3:
                return False

        parts = [p.strip() for p in cls.SPLIT_PATTERN.split(clean) if p.strip()]
        actionable_count = sum(1 for p in parts if any(p.lower().startswith(v) or f" {v} " in f" {p.lower()} " for v in cls.ACTION_VERBS))
        return len(parts) >= 2 and actionable_count >= 2

    @classmethod
    def parse_plan(cls, text: str) -> List[ExecutionStep]:
        """Parse compound command into discrete ExecutionSteps."""
        clean = text.strip()
        raw_parts = [p.strip() for p in cls.SPLIT_PATTERN.split(clean) if p.strip()]

        steps: List[ExecutionStep] = []
        for idx, part in enumerate(raw_parts, start=1):
            lower = part.lower()
            depends = False
            # Check for referring pronouns "it", "that file", "the report"
            if idx > 1 and any(w in lower for w in [" it", " that", " the file", " the folder"]):
                depends = True

            steps.append(ExecutionStep(step_number=idx, instruction=part, depends_on_previous=depends))

        return steps

    @staticmethod
    async def execute_plan(steps: List[ExecutionStep]) -> ChatResponse:
        """Execute each step in the plan, verifying results sequentially without conversational clutter."""
        from app.ai.provider import check_fast_path_action

        executed_tool_calls: List[ToolCallDetail] = []
        step_summaries: List[str] = []
        failed_summaries: List[str] = []
        previous_result: Optional[Dict[str, Any]] = None
        all_success = True
        launched_browser: Optional[str] = None

        for step in steps:
            logger.info(f"Executing Plan Step {step.step_number}: '{step.instruction}'")

            # Resolve dependent targets if previous step produced a path/file
            instruction = step.instruction
            if step.depends_on_previous and previous_result:
                target_path = (
                    previous_result.get("target_path")
                    or previous_result.get("path")
                    or (previous_result.get("matches", [None])[0] if isinstance(previous_result.get("matches"), list) and previous_result.get("matches") else None)
                )
                if target_path and "open" in instruction.lower():
                    instruction = f"open {target_path}"

            # Track if a browser was launched in this multi-step plan
            if "chrome" in instruction.lower() and any(w in instruction.lower() for w in ["open", "launch"]):
                launched_browser = "chrome"

            # Fast-path resolution for the sub-instruction
            response = await check_fast_path_action(instruction, preferred_browser=launched_browser)

            if response and response.status == "success":
                step.executed = True
                step.success = True
                executed_tool_calls.extend(response.tool_calls)
                # Extract first tool result for potential chaining
                if response.tool_calls:
                    previous_result = response.tool_calls[-1].result

                # Clean message for natural direct obedience without "Step 1" prefixes
                raw_msg = response.message.strip()
                clean_msg = re.sub(r'^(?:at your service,\s*sir\.?\s*|done,\s*sir\.?\s*)', '', raw_msg, flags=re.IGNORECASE)
                clean_msg = re.sub(r'[,.]?\s*sir\.?$', '', clean_msg, flags=re.IGNORECASE).strip()
                clean_msg = clean_msg.rstrip('.')
                step_summaries.append(clean_msg)
            else:
                step.executed = True
                step.success = False
                all_success = False
                err_msg = response.message if response else f"Unable to resolve directive: '{step.instruction}'"
                err_clean = re.sub(r'[,.]?\s*sir\.?$', '', err_msg, flags=re.IGNORECASE).strip().rstrip('.')
                failed_summaries.append(f"could not {step.instruction} ({err_clean})")

                if step.depends_on_previous:
                    break

        if all_success:
            if not step_summaries:
                summary_text = "Directives executed, sir."
            elif len(step_summaries) == 1:
                summary_text = f"{step_summaries[0]}, sir."
            elif len(step_summaries) == 2:
                summary_text = f"{step_summaries[0]}, and {step_summaries[1].lower()}, sir."
            else:
                joined = ", ".join(step_summaries[:-1]) + f", and {step_summaries[-1].lower()}"
                summary_text = f"{joined}, sir."
        else:
            if step_summaries and failed_summaries:
                summary_text = f"{'; '.join(step_summaries)}, but {'; '.join(failed_summaries)}, sir."
            else:
                summary_text = f"Encountered an issue: {'; '.join(failed_summaries)}, sir."

        return ChatResponse(
            conversation_id="",
            message=summary_text,
            tool_calls=executed_tool_calls,
            status="success" if all_success else "partial"
        )

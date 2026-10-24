import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { JarvisState } from '../types';

interface AICoreProps {
  state: JarvisState;
  reducedMotion?: boolean;
  audioLevel?: number; // 0 to 1
  onClick?: () => void;
}

export const AICore: React.FC<AICoreProps> = ({
  state,
  reducedMotion = false,
  audioLevel = 0,
  onClick
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const [webglSupported, setWebglSupported] = useState<boolean>(true);

  // References to animate
  const ringsRef = useRef<THREE.Group[]>([]);
  const coilsGroupRef = useRef<THREE.Group | null>(null);
  const coreSphereRef = useRef<THREE.Mesh | null>(null);
  const wireSphereRef = useRef<THREE.Mesh | null>(null);
  const particlesRef = useRef<THREE.Points | null>(null);
  const coreLightRef = useRef<THREE.PointLight | null>(null);
  const waveformRaysRef = useRef<THREE.LineSegments | null>(null);

  const stateColorRef = useRef<THREE.Color>(new THREE.Color(0x00f0ff));
  const targetColorRef = useRef<THREE.Color>(new THREE.Color(0x00f0ff));
  const speedMultiplierRef = useRef<number>(1);

  // Mouse parallax tracking
  const mouseRef = useRef<{ x: number; y: number; targetX: number; targetY: number }>({
    x: 0,
    y: 0,
    targetX: 0,
    targetY: 0
  });

  // Determine target colors & speeds according to JarvisState
  useEffect(() => {
    switch (state) {
      case 'listening':
        targetColorRef.current.setHex(0x00f0ff);
        speedMultiplierRef.current = 1.4;
        break;
      case 'processing':
      case 'thinking':
        targetColorRef.current.setHex(0x38bdf8);
        speedMultiplierRef.current = 2.4;
        break;
      case 'speaking':
        targetColorRef.current.setHex(0x22d3ee);
        speedMultiplierRef.current = 1.8;
        break;
      case 'executing_tool':
        targetColorRef.current.setHex(0x06b6d4);
        speedMultiplierRef.current = 2.8;
        break;
      case 'awaiting_approval':
        targetColorRef.current.setHex(0xf59e0b); // Amber
        speedMultiplierRef.current = 0.8;
        break;
      case 'success':
        targetColorRef.current.setHex(0x10b981); // Emerald
        speedMultiplierRef.current = 1.5;
        break;
      case 'error':
        targetColorRef.current.setHex(0xef4444); // Crimson
        speedMultiplierRef.current = 0.5;
        break;
      case 'idle':
      default:
        targetColorRef.current.setHex(0x00f0ff);
        speedMultiplierRef.current = 1.0;
        break;
    }
  }, [state]);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // Check WebGL availability
    try {
      const testCanvas = document.createElement('canvas');
      const gl = testCanvas.getContext('webgl') || testCanvas.getContext('experimental-webgl');
      if (!gl) {
        setWebglSupported(false);
        return;
      }
    } catch {
      setWebglSupported(false);
      return;
    }

    const width = container.clientWidth || 400;
    const height = container.clientHeight || 400;

    // Scene, Camera, Renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.z = 8.5;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // Root Group for Mouse Parallax
    const rootGroup = new THREE.Group();
    scene.add(rootGroup);

    // Ambient & Core Point Lights
    const ambientLight = new THREE.AmbientLight(0x002233, 0.5);
    scene.add(ambientLight);

    const coreLight = new THREE.PointLight(0x00f0ff, 3, 12);
    rootGroup.add(coreLight);
    coreLightRef.current = coreLight;

    // 1. Central Core Energy Sphere (Arc Reactor Core)
    const coreGeo = new THREE.SphereGeometry(0.9, 32, 32);
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0x00f0ff,
      transparent: true,
      opacity: 0.65,
    });
    const coreSphere = new THREE.Mesh(coreGeo, coreMat);
    rootGroup.add(coreSphere);
    coreSphereRef.current = coreSphere;

    // Inner Glowing Plasma Orb
    const innerPlasmaGeo = new THREE.SphereGeometry(0.5, 24, 24);
    const innerPlasmaMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.9,
    });
    const innerPlasma = new THREE.Mesh(innerPlasmaGeo, innerPlasmaMat);
    rootGroup.add(innerPlasma);

    // Outer Faceted Wireframe Shell
    const wireGeo = new THREE.IcosahedronGeometry(1.3, 2);
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      wireframe: true,
      transparent: true,
      opacity: 0.45,
    });
    const wireSphere = new THREE.Mesh(wireGeo, wireMat);
    rootGroup.add(wireSphere);
    wireSphereRef.current = wireSphere;

    // 2. Iron Man Arc Reactor 10 Coils Array
    const coilsGroup = new THREE.Group();
    const coilCount = 10;
    const coilRadius = 1.7;

    for (let i = 0; i < coilCount; i++) {
      const angle = (i / coilCount) * Math.PI * 2;
      const coilBoxGeo = new THREE.BoxGeometry(0.18, 0.38, 0.15);
      const coilMat = new THREE.MeshBasicMaterial({
        color: 0x00f0ff,
        transparent: true,
        opacity: 0.85
      });
      const coilMesh = new THREE.Mesh(coilBoxGeo, coilMat);
      coilMesh.position.set(Math.cos(angle) * coilRadius, Math.sin(angle) * coilRadius, 0);
      coilMesh.rotation.z = angle + Math.PI / 2;
      coilsGroup.add(coilMesh);
    }
    rootGroup.add(coilsGroup);
    coilsGroupRef.current = coilsGroup;

    // 3. Concentric Holographic Rings (Gimbal System)
    ringsRef.current = [];
    const ringConfigs = [
      { radius: 2.05, tube: 0.018, seg: 64, rotSpeed: 0.012, axis: new THREE.Vector3(0, 0, 1) },
      { radius: 2.45, tube: 0.015, seg: 64, rotSpeed: -0.015, axis: new THREE.Vector3(0.3, 1, 0.2) },
      { radius: 2.85, tube: 0.012, seg: 80, rotSpeed: 0.008, axis: new THREE.Vector3(1, 0.2, 0.3) },
      { radius: 3.25, tube: 0.022, seg: 96, rotSpeed: -0.006, axis: new THREE.Vector3(0.5, 0.8, 1) },
    ];

    ringConfigs.forEach((cfg) => {
      const ringGroup = new THREE.Group();
      const torusGeo = new THREE.TorusGeometry(cfg.radius, cfg.tube, 8, cfg.seg);
      const torusMat = new THREE.MeshBasicMaterial({
        color: 0x00f0ff,
        transparent: true,
        opacity: 0.75,
      });
      const torus = new THREE.Mesh(torusGeo, torusMat);
      ringGroup.add(torus);

      // Add orbiting tick markers along the ring
      const markerCount = 6;
      for (let m = 0; m < markerCount; m++) {
        const angle = (m / markerCount) * Math.PI * 2;
        const markerGeo = new THREE.BoxGeometry(0.08, 0.08, 0.08);
        const markerMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
        const marker = new THREE.Mesh(markerGeo, markerMat);
        marker.position.set(Math.cos(angle) * cfg.radius, Math.sin(angle) * cfg.radius, 0);
        ringGroup.add(marker);
      }

      ringGroup.userData = { rotSpeed: cfg.rotSpeed, axis: cfg.axis, baseRadius: cfg.radius };
      rootGroup.add(ringGroup);
      ringsRef.current.push(ringGroup);
    });

    // 4. Outer Waveform Frequency Spokes (Sound reactive)
    const rayCount = 48;
    const rayPositions = new Float32Array(rayCount * 6);
    for (let i = 0; i < rayCount; i++) {
      const angle = (i / rayCount) * Math.PI * 2;
      const innerR = 3.35;
      const outerR = 3.55;
      const idx = i * 6;
      rayPositions[idx] = Math.cos(angle) * innerR;
      rayPositions[idx + 1] = Math.sin(angle) * innerR;
      rayPositions[idx + 2] = 0;
      rayPositions[idx + 3] = Math.cos(angle) * outerR;
      rayPositions[idx + 4] = Math.sin(angle) * outerR;
      rayPositions[idx + 5] = 0;
    }
    const rayGeo = new THREE.BufferGeometry();
    rayGeo.setAttribute('position', new THREE.BufferAttribute(rayPositions, 3));
    const rayMat = new THREE.LineBasicMaterial({ color: 0x00f0ff, transparent: true, opacity: 0.6 });
    const waveformRays = new THREE.LineSegments(rayGeo, rayMat);
    rootGroup.add(waveformRays);
    waveformRaysRef.current = waveformRays;

    // 5. Ambient Particle Galaxy
    const particleCount = 280;
    const particleGeo = new THREE.BufferGeometry();
    const posArray = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount * 3; i += 3) {
      const radius = 1.6 + Math.random() * 2.8;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      posArray[i] = radius * Math.sin(phi) * Math.cos(theta);
      posArray[i + 1] = radius * Math.sin(phi) * Math.sin(theta);
      posArray[i + 2] = radius * Math.cos(phi);
    }
    particleGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    const particleMat = new THREE.PointsMaterial({
      size: 0.045,
      color: 0x00f0ff,
      transparent: true,
      opacity: 0.7,
      blending: THREE.AdditiveBlending,
    });
    const particles = new THREE.Points(particleGeo, particleMat);
    rootGroup.add(particles);
    particlesRef.current = particles;

    // Mouse movement handler
    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      mouseRef.current.targetX = x * 0.45;
      mouseRef.current.targetY = y * 0.45;
    };
    window.addEventListener('mousemove', handleMouseMove);

    // Resize Observer
    const resizeObserver = new ResizeObserver(() => {
      if (!container) return;
      const newWidth = container.clientWidth;
      const newHeight = container.clientHeight;
      if (newWidth > 0 && newHeight > 0) {
        camera.aspect = newWidth / newHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(newWidth, newHeight);
      }
    });
    resizeObserver.observe(container);

    // Animation Loop
    let animationFrameId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      clock.getDelta();
      const elapsedTime = clock.getElapsedTime();

      // Smooth color transitions
      stateColorRef.current.lerp(targetColorRef.current, 0.06);
      const currentColorHex = stateColorRef.current.getHex();

      if (coreLightRef.current) {
        coreLightRef.current.color.set(currentColorHex);
        coreLightRef.current.intensity = 2.5 + (audioLevel * 4);
      }

      // Update central core scale & colors
      if (coreSphereRef.current) {
        (coreSphereRef.current.material as THREE.MeshBasicMaterial).color.set(currentColorHex);
        const pulse = Math.sin(elapsedTime * 2.5 * speedMultiplierRef.current) * 0.08 + (audioLevel * 0.45);
        coreSphereRef.current.scale.set(1 + pulse, 1 + pulse, 1 + pulse);
      }

      if (wireSphereRef.current) {
        (wireSphereRef.current.material as THREE.MeshBasicMaterial).color.set(currentColorHex);
        wireSphereRef.current.rotation.x += 0.006 * speedMultiplierRef.current;
        wireSphereRef.current.rotation.y += 0.009 * speedMultiplierRef.current;
      }

      // Rotate Arc Reactor Coils
      if (coilsGroupRef.current) {
        coilsGroupRef.current.rotation.z += 0.008 * speedMultiplierRef.current;
        coilsGroupRef.current.children.forEach((coil) => {
          if (coil instanceof THREE.Mesh && coil.material instanceof THREE.MeshBasicMaterial) {
            coil.material.color.set(currentColorHex);
          }
        });
      }

      // Rotate Waveform frequency spokes & scale with audio
      if (waveformRaysRef.current) {
        (waveformRaysRef.current.material as THREE.LineBasicMaterial).color.set(currentColorHex);
        waveformRaysRef.current.rotation.z -= 0.005 * speedMultiplierRef.current;
        const waveScale = 1 + (audioLevel * 0.4);
        waveformRaysRef.current.scale.set(waveScale, waveScale, 1);
      }

      if (particlesRef.current) {
        (particlesRef.current.material as THREE.PointsMaterial).color.set(currentColorHex);
        particlesRef.current.rotation.y += 0.0015 * speedMultiplierRef.current;
      }

      // Rotate concentric rings
      ringsRef.current.forEach((ring) => {
        const { rotSpeed, axis } = ring.userData;
        const currentSpeed = (reducedMotion ? rotSpeed * 0.2 : rotSpeed) * speedMultiplierRef.current;
        ring.rotateOnAxis(axis, currentSpeed);

        ring.children.forEach((child) => {
          if (child instanceof THREE.Mesh && child.material instanceof THREE.MeshBasicMaterial) {
            child.material.color.set(currentColorHex);
          }
        });
      });

      // Mouse Parallax interpolation
      if (!reducedMotion) {
        mouseRef.current.x += (mouseRef.current.targetX - mouseRef.current.x) * 0.06;
        mouseRef.current.y += (mouseRef.current.targetY - mouseRef.current.y) * 0.06;
        rootGroup.rotation.y = mouseRef.current.x;
        rootGroup.rotation.x = -mouseRef.current.y;
      }

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('mousemove', handleMouseMove);
      resizeObserver.disconnect();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [reducedMotion]);

  if (!webglSupported) {
    return (
      <div
        onClick={onClick}
        className="w-full h-full flex flex-col items-center justify-center cursor-pointer p-6"
      >
        <div className="w-52 h-52 rounded-full border-4 border-cyan-400/40 flex items-center justify-center animate-pulse shadow-[0_0_60px_rgba(0,240,255,0.4)]">
          <div className="w-36 h-36 rounded-full border-2 border-cyan-300/60 flex items-center justify-center">
            <div className="w-20 h-20 rounded-full bg-cyan-400/30 flex items-center justify-center">
              <span className="text-xs font-mono tracking-widest text-cyan-200 uppercase">{state}</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={mountRef}
      onClick={onClick}
      className="w-full h-full min-h-[380px] flex items-center justify-center cursor-pointer relative"
      title={`JARVIS Arc Reactor Core State: ${state}`}
    />
  );
};

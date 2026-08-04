"use client";

import React, { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Points, PointMaterial } from "@react-three/drei";
import * as THREE from "three";

// Deterministic seedable pseudo-random number generator
function createPRNG(seed: number) {
  let s = seed;
  return () => {
    s = (1103515245 * s + 12345) % 2147483648;
    return s / 2147483648;
  };
}

function ParticleField() {
  const ref = useRef<THREE.Points>(null);

  // Generate 2000 points uniformly distributed in a sphere
  const sphere = useMemo(() => {
    const rand = createPRNG(99);
    const points = new Float32Array(2000 * 3);
    for (let i = 0; i < 2000; i++) {
      const u = rand();
      const v = rand();
      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);
      const r = Math.cbrt(rand()) * 1.5;
      const idx = i * 3;
      points[idx] = r * Math.sin(phi) * Math.cos(theta);
      points[idx + 1] = r * Math.sin(phi) * Math.sin(theta);
      points[idx + 2] = r * Math.cos(phi);
    }
    return points;
  }, []);

  useFrame((state, delta) => {
    if (ref.current) {
      ref.current.rotation.x -= delta / 12;
      ref.current.rotation.y -= delta / 18;
    }
  });

  return (
    <group rotation={[0, 0, Math.PI / 4]}>
      <Points ref={ref} positions={sphere} stride={3} frustumCulled={false}>
        <PointMaterial
          transparent
          color="#a855f7"
          size={0.003}
          sizeAttenuation={true}
          depthWrite={false}
          opacity={0.6}
        />
      </Points>
    </group>
  );
}

export const ParticlesBackground: React.FC = () => {
  return (
    <div className="absolute inset-0 -z-20 w-full h-full overflow-hidden bg-[#030305]">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(120,119,198,0.06),transparent_70%)]" />
      <div className="absolute inset-0 bg-grid radial-gradient-mask" />
      <Canvas camera={{ position: [0, 0, 1] }}>
        <ParticleField />
      </Canvas>
    </div>
  );
};

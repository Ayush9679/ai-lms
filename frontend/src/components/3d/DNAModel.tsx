"use client";

import React, { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Line } from "@react-three/drei";
import * as THREE from "three";

function DoubleHelix() {
  const groupRef = useRef<THREE.Group>(null);

  // Generate DNA double helix strands and base pair bridges
  const [nodes, bridges] = useMemo(() => {
    const tempNodes: Array<{ pos: [number, number, number]; isStrandA: boolean }> = [];
    const tempBridges: Array<{ p1: [number, number, number]; p2: [number, number, number] }> = [];
    const steps = 36;
    const heightSpan = 2.2;
    const radius = 0.45;

    for (let i = 0; i <= steps; i++) {
      const fraction = i / steps;
      const y = (fraction - 0.5) * heightSpan;
      const angle = fraction * Math.PI * 4.5; // helix turns

      // Strand A coordinates
      const xA = Math.cos(angle) * radius;
      const zA = Math.sin(angle) * radius;

      // Strand B coordinates (180 degrees phase shift)
      const xB = Math.cos(angle + Math.PI) * radius;
      const zB = Math.sin(angle + Math.PI) * radius;

      tempNodes.push({ pos: [xA, y, zA], isStrandA: true });
      tempNodes.push({ pos: [xB, y, zB], isStrandA: false });

      // Connect strand A and B periodically (rungs of the ladder)
      if (i % 2 === 0) {
        tempBridges.push({
          p1: [xA, y, zA],
          p2: [xB, y, zB],
        });
      }
    }

    return [tempNodes, tempBridges];
  }, []);

  useFrame((state, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.4;
      groupRef.current.rotation.x = Math.sin(state.clock.getElapsedTime() * 0.5) * 0.15;
    }
  });

  return (
    <group ref={groupRef}>
      {/* Draw the ladder rungs */}
      {bridges.map((bridge, idx) => (
        <Line
          key={idx}
          points={[bridge.p1, bridge.p2]}
          color={idx % 2 === 0 ? "#ec4899" : "#3b82f6"}
          lineWidth={1.2}
          transparent
          opacity={0.5}
        />
      ))}

      {/* Draw the sugar-phosphate backbone node points */}
      {nodes.map((node, idx) => (
        <mesh key={idx} position={node.pos}>
          <sphereGeometry args={[0.04, 8, 8]} />
          <meshStandardMaterial
            color={node.isStrandA ? "#a855f7" : "#3b82f6"}
            emissive={node.isStrandA ? "#a855f7" : "#3b82f6"}
            emissiveIntensity={0.6}
            roughness={0.1}
          />
        </mesh>
      ))}
    </group>
  );
}

export const DNAModelCanvas: React.FC = () => {
  return (
    <div className="w-full h-[260px] md:h-[350px]">
      <Canvas camera={{ position: [0, 0, 1.8], fov: 50 }}>
        <ambientLight intensity={0.6} />
        <pointLight position={[10, 10, 10]} intensity={1.5} color="#a855f7" />
        <pointLight position={[-10, -10, -10]} intensity={1} color="#3b82f6" />
        <DoubleHelix />
        <OrbitControls enableZoom={false} enablePan={false} />
      </Canvas>
    </div>
  );
};
export default DNAModelCanvas;

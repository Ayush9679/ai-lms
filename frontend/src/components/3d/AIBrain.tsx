"use client";

import React, { useRef, useMemo } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, Line } from "@react-three/drei";
import * as THREE from "three";

// Deterministic seedable pseudo-random number generator
function createPRNG(seed: number) {
  let s = seed;
  return () => {
    s = (1103515245 * s + 12345) % 2147483648;
    return s / 2147483648;
  };
}

function BrainNodeNetwork() {
  const groupRef = useRef<THREE.Group>(null);
  const { pointer } = useThree();

  // Generate nodes inside two ellipsoids representing brain lobes
  const [nodes, lines] = useMemo(() => {
    const rand = createPRNG(42);
    const tempNodes: Array<[number, number, number]> = [];
    const tempLines: Array<Array<number>> = [];
    const lobes = [-0.35, 0.35]; // Left and right lobes offset

    lobes.forEach((xOffset) => {
      for (let i = 0; i < 90; i++) {
        // Spherical distribution mapped to shape like a cerebral hemisphere
        const theta = rand() * Math.PI * 2;
        const phi = Math.acos(rand() * 2 - 1);
        const r = Math.cbrt(rand()) * 0.7;

        // Add wrinkles/ridges to the lobes
        const rx = 0.5 * (1 + 0.15 * Math.sin(theta * 6) * Math.cos(phi * 4));
        const ry = 0.65 * (1 + 0.15 * Math.sin(theta * 4) * Math.sin(phi * 6));
        const rz = 0.55 * (1 + 0.15 * Math.cos(theta * 5));

        const x = r * rx * Math.sin(phi) * Math.cos(theta) + xOffset;
        const y = r * ry * Math.sin(phi) * Math.sin(theta) + 0.1;
        const z = r * rz * Math.cos(phi);

        tempNodes.push([x, y, z]);
      }
    });

    // Create brain stem / cerebellum structure
    for (let i = 0; i < 40; i++) {
      const z = (rand() - 0.5) * 0.4;
      const theta = rand() * Math.PI * 2;
      const r = rand() * 0.25;
      const x = r * Math.cos(theta);
      const y = -0.4 - rand() * 0.3; // stem dropping down
      tempNodes.push([x, y, z]);
    }

    // Connect close neighbors
    for (let i = 0; i < tempNodes.length; i++) {
      let connections = 0;
      for (let j = i + 1; j < tempNodes.length; j++) {
        const dx = tempNodes[i][0] - tempNodes[j][0];
        const dy = tempNodes[i][1] - tempNodes[j][1];
        const dz = tempNodes[i][2] - tempNodes[j][2];
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);

        // Don't connect left & right lobes directly except via corpus callosum
        const areInOppositeLobes =
          (tempNodes[i][0] > 0.1 && tempNodes[j][0] < -0.1) ||
          (tempNodes[i][0] < -0.1 && tempNodes[j][0] > 0.1);

        const limit = areInOppositeLobes ? 0.18 : 0.26;

        if (dist < limit && connections < 3) {
          tempLines.push([
            tempNodes[i][0],
            tempNodes[i][1],
            tempNodes[i][2],
            tempNodes[j][0],
            tempNodes[j][1],
            tempNodes[j][2],
          ]);
          connections++;
        }
      }
    }

    return [tempNodes, tempLines];
  }, []);

  useFrame((state, delta) => {
    if (groupRef.current) {
      // Slow rotation
      groupRef.current.rotation.y += delta * 0.18;
      
      // Mouse interaction: lean towards pointer coordinates
      const targetX = pointer.x * 0.35;
      const targetY = pointer.y * 0.35;
      groupRef.current.rotation.x = THREE.MathUtils.lerp(groupRef.current.rotation.x, targetY, 0.05);
      groupRef.current.rotation.z = THREE.MathUtils.lerp(groupRef.current.rotation.z, -targetX, 0.05);
    }
  });

  return (
    <group ref={groupRef}>
      {/* Draw neural connection pathways */}
      {lines.map((line, idx) => (
        <Line
          key={idx}
          points={[
            [line[0], line[1], line[2]],
            [line[3], line[4], line[5]],
          ]}
          color={idx % 2 === 0 ? "#a855f7" : "#3b82f6"}
          lineWidth={0.7}
          transparent
          opacity={0.35}
        />
      ))}

      {/* Draw glowing neural node points */}
      {nodes.map((node, idx) => (
        <mesh key={idx} position={node}>
          <sphereGeometry args={[idx % 5 === 0 ? 0.015 : 0.009, 6, 6]} />
          <meshBasicMaterial
            color={idx % 3 === 0 ? "#ec4899" : idx % 2 === 0 ? "#3b82f6" : "#a855f7"}
            transparent
            opacity={0.8}
          />
        </mesh>
      ))}
    </group>
  );
}

export const AIBrainCanvas: React.FC = () => {
  return (
    <div className="w-full h-[320px] md:h-[450px] cursor-grab active:cursor-grabbing">
      <Canvas camera={{ position: [0, 0, 2.2], fov: 60 }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1.5} color="#a855f7" />
        <pointLight position={[-10, -10, -10]} intensity={1} color="#3b82f6" />
        <BrainNodeNetwork />
        <OrbitControls enableZoom={false} enablePan={false} autoRotate={false} />
      </Canvas>
    </div>
  );
};
export default AIBrainCanvas;

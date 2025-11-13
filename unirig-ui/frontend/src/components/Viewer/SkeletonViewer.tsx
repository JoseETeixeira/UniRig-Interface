import React, { useState } from 'react';
import { useLoader } from '@react-three/fiber';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import * as THREE from 'three';

interface SkeletonViewerProps {
  modelUrl: string;
  skeletonUrl?: string;
  showSkeleton?: boolean;
  onBoneHover?: (boneName: string | null) => void;
}

/**
 * Component for displaying skeleton structure with bone highlighting
 */
export const SkeletonViewer: React.FC<SkeletonViewerProps> = ({
  modelUrl,
  skeletonUrl,
  showSkeleton = true,
  onBoneHover,
}) => {
  const modelGltf = useLoader(GLTFLoader, modelUrl);
  const skeletonGltf = skeletonUrl ? useLoader(GLTFLoader, skeletonUrl) : null;
  const [hoveredBone, setHoveredBone] = useState<string | null>(null);

  // Create bone visualization
  const createBoneVisualization = (scene: THREE.Object3D) => {
    const group = new THREE.Group();
    const material = new THREE.LineBasicMaterial({ 
      color: 0x00ff00,
      linewidth: 2,
    });
    const highlightMaterial = new THREE.LineBasicMaterial({ 
      color: 0xffff00,
      linewidth: 3,
    });

    scene.traverse((object) => {
      if (object instanceof THREE.Bone && object.parent instanceof THREE.Bone) {
        const points = [
          object.parent.getWorldPosition(new THREE.Vector3()),
          object.getWorldPosition(new THREE.Vector3()),
        ];
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        const line = new THREE.Line(
          geometry,
          hoveredBone === object.name ? highlightMaterial : material
        );
        line.userData.boneName = object.name;
        group.add(line);

        // Add sphere at joint
        const sphereGeometry = new THREE.SphereGeometry(0.02, 8, 8);
        const sphereMaterial = new THREE.MeshBasicMaterial({
          color: hoveredBone === object.name ? 0xffff00 : 0x00ff00,
        });
        const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
        sphere.position.copy(object.getWorldPosition(new THREE.Vector3()));
        sphere.userData.boneName = object.name;
        group.add(sphere);
      }
    });

    return group;
  };

  const handlePointerMove = (event: any) => {
    if (event.object.userData.boneName) {
      setHoveredBone(event.object.userData.boneName);
      if (onBoneHover) {
        onBoneHover(event.object.userData.boneName);
      }
    }
  };

  const handlePointerOut = () => {
    setHoveredBone(null);
    if (onBoneHover) {
      onBoneHover(null);
    }
  };

  return (
    <group>
      {/* Original Model */}
      <primitive
        object={modelGltf.scene.clone()}
        scale={1}
        onPointerMove={handlePointerMove}
        onPointerOut={handlePointerOut}
      />

      {/* Skeleton Overlay */}
      {showSkeleton && skeletonGltf && (
        <primitive
          object={createBoneVisualization(skeletonGltf.scene)}
          onPointerMove={handlePointerMove}
          onPointerOut={handlePointerOut}
        />
      )}
    </group>
  );
};

/**
 * Bone name tooltip component
 */
interface BoneTooltipProps {
  boneName: string | null;
}

export const BoneTooltip: React.FC<BoneTooltipProps> = ({ boneName }) => {
  if (!boneName) return null;

  return (
    <div className="absolute top-4 right-4 bg-black bg-opacity-75 text-white px-3 py-2 rounded-lg text-sm">
      <span className="font-medium">Bone:</span> {boneName}
    </div>
  );
};

import React, { useEffect, useRef, useState } from 'react';
import { useLoader, useFrame } from '@react-three/fiber';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import * as THREE from 'three';

interface SkinViewerProps {
  modelUrl: string;
  autoRotate?: boolean;
  showWireframe?: boolean;
}

/**
 * Component for displaying rigged model with animation support
 */
export const SkinViewer: React.FC<SkinViewerProps> = ({
  modelUrl,
  autoRotate = false,
  showWireframe = false,
}) => {
  const gltf = useLoader(GLTFLoader, modelUrl);
  const mixer = useRef<THREE.AnimationMixer | null>(null);
  const modelRef = useRef<THREE.Group>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    if (gltf.animations && gltf.animations.length > 0) {
      mixer.current = new THREE.AnimationMixer(gltf.scene);
      
      // Play first animation by default
      const action = mixer.current.clipAction(gltf.animations[0]);
      action.play();
      setIsPlaying(true);
    }
  }, [gltf]);

  // Update animation
  useFrame((_state, delta) => {
    if (mixer.current && isPlaying) {
      mixer.current.update(delta);
    }

    // Auto-rotate model
    if (autoRotate && modelRef.current) {
      modelRef.current.rotation.y += delta * 0.5;
    }
  });

  // Animation controls (for future implementation)
  // const playAnimation = (index: number) => {
  //   if (!mixer.current || !animations[index]) return;
  //   mixer.current.stopAllAction();
  //   const action = mixer.current.clipAction(animations[index]);
  //   action.play();
  //   setCurrentAnimation(index);
  //   setIsPlaying(true);
  // };

  // const togglePlayPause = () => {
  //   if (!mixer.current) return;
  //   if (isPlaying) {
  //     mixer.current.timeScale = 0;
  //   } else {
  //     mixer.current.timeScale = 1;
  //   }
  //   setIsPlaying(!isPlaying);
  // };

  return (
    <group ref={modelRef}>
      <primitive 
        object={gltf.scene.clone()} 
        scale={1}
      />
      {showWireframe && (
        <primitive 
          object={gltf.scene.clone()}
        >
          <meshBasicMaterial wireframe color="#00ff00" />
        </primitive>
      )}
    </group>
  );
};

/**
 * Animation controls component
 */
interface AnimationControlsProps {
  isPlaying: boolean;
  onPlayPause: () => void;
  animations: string[];
  currentAnimation: number;
  onAnimationChange: (index: number) => void;
}

export const AnimationControls: React.FC<AnimationControlsProps> = ({
  isPlaying,
  onPlayPause,
  animations,
  currentAnimation,
  onAnimationChange,
}) => {
  return (
    <div className="absolute bottom-4 left-4 right-4 bg-black bg-opacity-75 rounded-lg p-4">
      <div className="flex items-center space-x-4">
        {/* Play/Pause Button */}
        <button
          onClick={onPlayPause}
          className="p-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
        >
          {isPlaying ? (
            <svg
              className="w-6 h-6 text-white"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
          ) : (
            <svg
              className="w-6 h-6 text-white"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                clipRule="evenodd"
              />
            </svg>
          )}
        </button>

        {/* Animation Selector */}
        {animations.length > 0 && (
          <select
            value={currentAnimation}
            onChange={(e) => onAnimationChange(Number(e.target.value))}
            className="flex-1 bg-gray-800 text-white px-3 py-2 rounded-lg border border-gray-700"
          >
            {animations.map((name, index) => (
              <option key={index} value={index}>
                {name || `Animation ${index + 1}`}
              </option>
            ))}
          </select>
        )}
      </div>
    </div>
  );
};

/**
 * Weight heatmap visualization overlay
 */
interface WeightHeatmapProps {
  selectedBone: string | null;
  weights: number[];
}

export const WeightHeatmap: React.FC<WeightHeatmapProps> = ({
  selectedBone,
  weights,
}) => {
  if (!selectedBone) return null;

  return (
    <div className="absolute top-4 right-4 bg-black bg-opacity-75 text-white px-4 py-3 rounded-lg">
      <h3 className="text-sm font-medium mb-2">Skinning Weights: {selectedBone}</h3>
      <div className="flex items-center space-x-2">
        <span className="text-xs">Low</span>
        <div className="w-32 h-4 rounded bg-gradient-to-r from-blue-500 via-green-500 to-red-500"></div>
        <span className="text-xs">High</span>
      </div>
      <p className="text-xs text-gray-400 mt-2">
        Vertices influenced: {weights.length}
      </p>
    </div>
  );
};

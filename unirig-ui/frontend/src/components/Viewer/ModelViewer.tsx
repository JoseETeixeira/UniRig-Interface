import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Grid } from '@react-three/drei';

interface ModelViewerProps {
  children?: React.ReactNode;
  showGrid?: boolean;
  cameraPosition?: [number, number, number];
}

/**
 * Base 3D viewer component with camera, lighting, and controls
 */
export const ModelViewer: React.FC<ModelViewerProps> = ({
  children,
  showGrid = true,
  cameraPosition = [0, 1, 3],
}) => {
  return (
    <div className="w-full h-full min-h-[500px] bg-gray-900 rounded-lg overflow-hidden">
      <Canvas shadows>
        {/* Camera */}
        <PerspectiveCamera makeDefault position={cameraPosition} fov={50} />

        {/* Lighting */}
        <ambientLight intensity={0.5} />
        <directionalLight
          position={[10, 10, 5]}
          intensity={1}
          castShadow
          shadow-mapSize-width={1024}
          shadow-mapSize-height={1024}
        />
        <directionalLight position={[-10, 10, -5]} intensity={0.3} />

        {/* Controls */}
        <OrbitControls
          enableDamping
          dampingFactor={0.05}
          minDistance={0.5}
          maxDistance={10}
        />

        {/* Grid */}
        {showGrid && (
          <Grid
            args={[10, 10]}
            cellSize={0.5}
            cellThickness={0.5}
            cellColor="#6b7280"
            sectionSize={1}
            sectionThickness={1}
            sectionColor="#9ca3af"
            fadeDistance={25}
            fadeStrength={1}
            followCamera={false}
          />
        )}

        {/* Loading fallback */}
        <Suspense fallback={null}>{children}</Suspense>
      </Canvas>
    </div>
  );
};

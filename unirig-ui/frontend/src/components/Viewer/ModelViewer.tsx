import React, { Suspense, useState, useCallback, useRef, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Grid, Html } from '@react-three/drei';
import * as THREE from 'three';
import { Model } from './Model';
import { SkeletonHelper } from './SkeletonHelper';
import { ViewerControls } from './ViewerControls';
import { detectWebGLSupport, getWebGLErrorMessage } from '../../utils/webgl-detect';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';

interface ModelViewerProps {
  modelUrl?: string;
  modelFileSize?: number; // File size in bytes
  showGrid?: boolean;
  showSkeleton?: boolean;
  cameraPosition?: [number, number, number];
  onAnimationsLoaded?: (animations: THREE.AnimationClip[]) => void;
  children?: React.ReactNode;
}

/**
 * Loading indicator shown while model is being loaded
 */
function LoadingIndicator({ progress }: { progress: number }) {
  return (
    <Html center>
      <div className="bg-gray-800 text-white px-6 py-4 rounded-lg shadow-lg">
        <div className="text-center mb-2">Loading model...</div>
        <div className="w-48 h-2 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="text-center mt-2 text-sm text-gray-400">
          {Math.round(progress)}%
        </div>
      </div>
    </Html>
  );
}

/**
 * Enhanced 3D model viewer component with FBX/GLB loading support
 * 
 * Features:
 * - Loads and renders FBX and GLB model files
 * - Automatic model centering and scaling
 * - Orbit camera controls (rotate, pan, zoom)
 * - Loading states with progress indicator
 * - Error handling with user-friendly messages
 * - WebGL capability detection
 * - Proper lighting and shadows
 */
export const ModelViewer: React.FC<ModelViewerProps> = ({
  modelUrl,
  modelFileSize,
  showGrid = true,
  showSkeleton: showSkeletonProp = false,
  cameraPosition = [0, 1, 3],
  onAnimationsLoaded,
  children,
}) => {
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [loadingError, setLoadingError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadedModel, setLoadedModel] = useState<THREE.Group | null>(null);
  const [showSkeletonInternal, setShowSkeletonInternal] = useState(showSkeletonProp);
  const [wireframeMode, setWireframeMode] = useState(false);
  const [lightingIntensity, setLightingIntensity] = useState(1.0);
  const [backgroundColor, setBackgroundColor] = useState('#1f2937');
  const [showLargeFileWarning, setShowLargeFileWarning] = useState(false);
  const [loadFullQuality, setLoadFullQuality] = useState(false);
  const controlsRef = useRef<OrbitControlsImpl>(null);
  const defaultCameraPosition = useRef(cameraPosition);

  // Large file threshold: 50MB
  const LARGE_FILE_THRESHOLD = 50 * 1024 * 1024; // 50MB in bytes
  const isLargeFile = modelFileSize ? modelFileSize > LARGE_FILE_THRESHOLD : false;

  // Calculate default distance from origin for zoom limits
  const defaultDistance = Math.sqrt(
    cameraPosition[0] ** 2 + cameraPosition[1] ** 2 + cameraPosition[2] ** 2
  );
  const minZoomDistance = defaultDistance * 0.5; // 0.5x zoom (closer)
  const maxZoomDistance = defaultDistance * 5; // 5x zoom (farther)

  // Check WebGL support
  const capabilities = detectWebGLSupport();
  const webglError = getWebGLErrorMessage(capabilities);

  const handleModelLoad = useCallback((model: THREE.Group) => {
    setIsLoading(false);
    setLoadingError(null);
    setLoadedModel(model);
    console.log('Model loaded successfully:', model);
  }, []);

  const handleModelError = useCallback((error: Error) => {
    setIsLoading(false);
    setLoadingError(error.message);
    console.error('Model loading error:', error);
  }, []);

  const handleProgress = useCallback((progress: number) => {
    setIsLoading(true);
    setLoadingProgress(progress);
  }, []);

  const handleCameraReset = useCallback(() => {
    if (controlsRef.current) {
      // Reset camera position
      controlsRef.current.object.position.set(
        defaultCameraPosition.current[0],
        defaultCameraPosition.current[1],
        defaultCameraPosition.current[2]
      );
      // Reset target to origin
      controlsRef.current.target.set(0, 0, 0);
      // Update controls
      controlsRef.current.update();
    }
  }, []);

  const handleToggleSkeleton = useCallback(() => {
    setShowSkeletonInternal(prev => !prev);
  }, []);

  const handleWireframeToggle = useCallback(() => {
    setWireframeMode(prev => !prev);
  }, []);

  const handleLightingChange = useCallback((intensity: number) => {
    setLightingIntensity(intensity);
  }, []);

  const handleBackgroundChange = useCallback((color: string) => {
    setBackgroundColor(color);
  }, []);

  // Apply wireframe mode to loaded model
  useEffect(() => {
    if (loadedModel) {
      loadedModel.traverse((child) => {
        if ((child as THREE.Mesh).isMesh) {
          const mesh = child as THREE.Mesh;
          if (Array.isArray(mesh.material)) {
            mesh.material.forEach((mat) => {
              if ('wireframe' in mat) {
                (mat as THREE.MeshStandardMaterial).wireframe = wireframeMode;
              }
            });
          } else if (mesh.material && 'wireframe' in mesh.material) {
            (mesh.material as THREE.MeshStandardMaterial).wireframe = wireframeMode;
          }
        }
      });
    }
  }, [loadedModel, wireframeMode]);

  // Show large file warning when model URL changes and file is large
  useEffect(() => {
    if (modelUrl && isLargeFile && !loadFullQuality) {
      setShowLargeFileWarning(true);
    } else {
      setShowLargeFileWarning(false);
    }
  }, [modelUrl, isLargeFile, loadFullQuality]);

  const handleLoadFullQuality = () => {
    setLoadFullQuality(true);
    setShowLargeFileWarning(false);
  };

  const handleLoadSimplified = () => {
    setLoadFullQuality(false);
    setShowLargeFileWarning(false);
    // Model component will handle simplified loading
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  // Show WebGL error if not supported
  if (webglError) {
    return (
      <div className="w-full h-full min-h-[500px] bg-gray-900 rounded-lg overflow-hidden flex items-center justify-center p-6">
        <div className="text-center text-red-400 max-w-md">
          <div className="text-4xl mb-4">⚠️</div>
          <div className="text-lg font-semibold mb-2">WebGL Not Available</div>
          <div className="text-sm text-gray-400">{webglError}</div>
          {capabilities.hasWebGL && !capabilities.hasWebGL2 && (
            <div className="text-xs text-gray-500 mt-3">
              Detected: {capabilities.renderer} ({capabilities.version})
            </div>
          )}
        </div>
      </div>
    );
  }

  // Show loading error
  if (loadingError) {
    return (
      <div className="w-full h-full min-h-[500px] bg-gray-900 rounded-lg overflow-hidden flex items-center justify-center p-6">
        <div className="text-center text-red-400 max-w-md">
          <div className="text-4xl mb-4">❌</div>
          <div className="text-lg font-semibold mb-2">Failed to Load Model</div>
          <div className="text-sm text-gray-400 mb-4">{loadingError}</div>
          <div className="text-xs text-gray-500">
            <p className="mb-1">Troubleshooting steps:</p>
            <ul className="list-disc list-inside text-left">
              <li>Verify the model file exists and is accessible</li>
              <li>Check that the file format is FBX or GLB</li>
              <li>Ensure the file is not corrupted</li>
              <li>Try refreshing the page</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full min-h-[500px] bg-gray-900 rounded-lg overflow-hidden relative">
      {/* Large File Warning Banner */}
      {showLargeFileWarning && modelFileSize && (
        <div className="absolute top-0 left-0 right-0 z-50 bg-yellow-100 dark:bg-yellow-900 border-b-2 border-yellow-400 dark:border-yellow-600 p-4">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 text-yellow-600 dark:text-yellow-400">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-yellow-800 dark:text-yellow-200 mb-1">
                Large Model File Detected
              </h3>
              <p className="text-xs text-yellow-700 dark:text-yellow-300 mb-3">
                This model is {formatFileSize(modelFileSize)}. Loading the full quality model may take longer and use more memory.
              </p>
              <div className="flex gap-2">
                <button
                  onClick={handleLoadSimplified}
                  className="px-4 py-2 text-xs font-medium text-yellow-900 dark:text-yellow-100 bg-yellow-200 dark:bg-yellow-700 hover:bg-yellow-300 dark:hover:bg-yellow-600 rounded transition-colors"
                >
                  Load Simplified (Faster)
                </button>
                <button
                  onClick={handleLoadFullQuality}
                  className="px-4 py-2 text-xs font-medium text-gray-700 dark:text-gray-200 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 rounded transition-colors"
                >
                  Load Full Quality
                </button>
              </div>
            </div>
            <button
              onClick={() => setShowLargeFileWarning(false)}
              className="flex-shrink-0 text-yellow-600 dark:text-yellow-400 hover:text-yellow-800 dark:hover:text-yellow-200"
              aria-label="Close warning"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      <Canvas shadows style={{ background: backgroundColor }}>
        {/* Camera */}
        <PerspectiveCamera makeDefault position={cameraPosition} fov={50} />

        {/* Lighting */}
        <ambientLight intensity={0.5 * lightingIntensity} />
        <directionalLight
          position={[10, 10, 5]}
          intensity={1 * lightingIntensity}
          castShadow
          shadow-mapSize-width={1024}
          shadow-mapSize-height={1024}
        />
        <directionalLight position={[-10, 10, -5]} intensity={0.3 * lightingIntensity} />
        <pointLight position={[0, 5, 0]} intensity={0.3 * lightingIntensity} />

        {/* Controls */}
        <OrbitControls
          ref={controlsRef}
          enableDamping
          dampingFactor={0.05}
          minDistance={minZoomDistance}
          maxDistance={maxZoomDistance}
          maxPolarAngle={Math.PI * 0.9}
          rotateSpeed={0.5}
          panSpeed={0.5}
          zoomSpeed={0.8}
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          touches={{
            ONE: THREE.TOUCH.ROTATE,
            TWO: THREE.TOUCH.DOLLY_PAN,
          }}
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

        {/* Loading indicator */}
        <Suspense fallback={<LoadingIndicator progress={loadingProgress} />}>
          {/* Load model if URL provided */}
          {modelUrl && (
            <Model
              url={modelUrl}
              onLoad={handleModelLoad}
              onError={handleModelError}
              onProgress={handleProgress}
              onAnimationsLoaded={onAnimationsLoaded}
              loadFullQuality={loadFullQuality}
            />
          )}
          
          {/* Skeleton overlay */}
          {loadedModel && (
            <SkeletonHelper
              model={loadedModel}
              visible={showSkeletonInternal}
              color="#00ff00"
              lineWidth={2}
            />
          )}
          
          {/* Custom children (for legacy support) */}
          {children}
        </Suspense>
      </Canvas>

      {/* Status overlay */}
      {isLoading && (
        <div className="absolute bottom-4 right-4 bg-gray-800 text-white px-3 py-2 rounded text-sm">
          Loading... {Math.round(loadingProgress)}%
        </div>
      )}

      {/* Camera reset button */}
      {!isLoading && !loadingError && (
        <div className="absolute top-4 right-4 flex gap-2">
          <button
            onClick={handleCameraReset}
            className="bg-gray-800 hover:bg-gray-700 text-white px-3 py-2 rounded text-sm transition-colors duration-200 flex items-center gap-2"
            title="Reset camera to default view"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Reset View
          </button>
          
          {/* Skeleton toggle button */}
          {loadedModel && (
            <button
              onClick={handleToggleSkeleton}
              className={`px-3 py-2 rounded text-sm transition-colors duration-200 flex items-center gap-2 ${
                showSkeletonInternal
                  ? 'bg-green-600 hover:bg-green-700 text-white'
                  : 'bg-gray-800 hover:bg-gray-700 text-white'
              }`}
              title="Toggle skeleton visualization"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
              Skeleton
            </button>
          )}
        </div>
      )}

      {/* WebGL info overlay */}
      {!isLoading && !loadingError && (
        <div className="absolute bottom-4 right-4 bg-gray-800 bg-opacity-80 text-white px-3 py-2 rounded text-xs font-mono">
          {capabilities.hasWebGL2 ? '✓ WebGL 2.0' : '⚠ WebGL 1.0'} | {capabilities.renderer}
        </div>
      )}

      {/* Viewer Controls Panel */}
      {!isLoading && !loadingError && loadedModel && (
        <ViewerControls
          wireframeMode={wireframeMode}
          onWireframeToggle={handleWireframeToggle}
          lightingIntensity={lightingIntensity}
          onLightingChange={handleLightingChange}
          backgroundColor={backgroundColor}
          onBackgroundChange={handleBackgroundChange}
        />
      )}
    </div>
  );
};

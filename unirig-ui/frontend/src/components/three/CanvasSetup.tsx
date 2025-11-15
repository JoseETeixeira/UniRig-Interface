/**
 * Basic Three.js canvas setup component.
 * Verifies React Three Fiber integration and provides a simple 3D scene.
 */

import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Box, Html } from '@react-three/drei';
import { detectWebGLSupport, getWebGLErrorMessage } from '../../utils/webgl-detect';

interface CanvasSetupProps {
  width?: number | string;
  height?: number | string;
  showTestCube?: boolean;
}

/**
 * Loading fallback component displayed while 3D content loads.
 */
function LoadingFallback() {
  return (
    <Html center>
      <div style={{
        padding: '20px',
        background: 'rgba(0, 0, 0, 0.8)',
        borderRadius: '8px',
        color: 'white',
        textAlign: 'center'
      }}>
        <div>Loading 3D scene...</div>
        <div style={{ marginTop: '10px', fontSize: '12px', opacity: 0.7 }}>
          Initializing WebGL renderer
        </div>
      </div>
    </Html>
  );
}

/**
 * Test cube component to verify Three.js rendering.
 */
function TestCube() {
  return (
    <Box args={[1, 1, 1]} position={[0, 0, 0]}>
      <meshStandardMaterial color="hotpink" />
    </Box>
  );
}

/**
 * Basic Three.js canvas setup component.
 * Provides a configured React Three Fiber Canvas with camera controls and lighting.
 * 
 * @param props - Component props
 * @returns Canvas component or error message if WebGL not supported
 */
export const CanvasSetup: React.FC<CanvasSetupProps> = ({ 
  width = '100%', 
  height = '400px',
  showTestCube = true 
}) => {
  // Detect WebGL support
  const capabilities = detectWebGLSupport();
  const errorMessage = getWebGLErrorMessage(capabilities);

  // Show error if WebGL not supported
  if (errorMessage) {
    return (
      <div style={{
        width,
        height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#1a1a1a',
        borderRadius: '8px',
        padding: '20px',
        color: '#ff6b6b'
      }}>
        <div style={{ textAlign: 'center', maxWidth: '500px' }}>
          <div style={{ fontSize: '24px', marginBottom: '10px' }}>⚠️</div>
          <div style={{ fontWeight: 'bold', marginBottom: '10px' }}>
            WebGL Not Available
          </div>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>
            {errorMessage}
          </div>
          {capabilities.hasWebGL && !capabilities.hasWebGL2 && (
            <div style={{ fontSize: '12px', marginTop: '15px', opacity: 0.7 }}>
              Detected: {capabilities.renderer} ({capabilities.version})
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div style={{ width, height }}>
      <Canvas
        camera={{
          position: [0, 0, 5],
          fov: 50,
          near: 0.1,
          far: 1000
        }}
        style={{
          width: '100%',
          height: '100%',
          background: '#1a1a1a'
        }}
      >
        {/* Lighting */}
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={1} />
        <pointLight position={[-10, -10, -5]} intensity={0.5} />

        {/* Camera controls */}
        <OrbitControls
          enableDamping
          dampingFactor={0.05}
          rotateSpeed={0.5}
          zoomSpeed={0.8}
          minDistance={2}
          maxDistance={20}
        />

        {/* Suspense boundary for lazy loading */}
        <Suspense fallback={<LoadingFallback />}>
          {showTestCube && <TestCube />}
        </Suspense>

        {/* Grid helper for reference */}
        <gridHelper args={[10, 10, 0x444444, 0x222222]} />
      </Canvas>
      
      {/* WebGL info overlay */}
      <div style={{
        position: 'absolute',
        bottom: '10px',
        right: '10px',
        background: 'rgba(0, 0, 0, 0.7)',
        color: 'white',
        padding: '8px 12px',
        borderRadius: '4px',
        fontSize: '11px',
        fontFamily: 'monospace'
      }}>
        {capabilities.hasWebGL2 ? '✓ WebGL 2.0' : '⚠ WebGL 1.0'} | {capabilities.renderer}
      </div>
    </div>
  );
};

export default CanvasSetup;

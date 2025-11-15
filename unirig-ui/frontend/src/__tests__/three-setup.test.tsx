/**
 * Three.js Setup Verification
 * 
 * This file verifies that Three.js and React Three Fiber dependencies
 * are properly installed and can be imported without errors.
 * 
 * Manual verification steps:
 * 1. Run `npm run dev` to start the development server
 * 2. Create a page that renders <CanvasSetup />
 * 3. Verify the pink test cube renders in the browser
 * 4. Verify WebGL info overlay appears in bottom-right
 * 5. Test orbit controls (drag to rotate, scroll to zoom)
 * 
 * Automated verification (when test framework is added):
 * - WebGL detection functions work correctly
 * - Three.js core library imports successfully
 * - FBXLoader and GLTFLoader can be imported
 * - React Three Fiber Canvas component is available
 * - @react-three/drei helpers are accessible
 */

// Verification imports - these should not throw errors
import * as THREE from 'three';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Box, Html } from '@react-three/drei';
import { FBXLoader } from 'three/addons/loaders/FBXLoader.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { detectWebGLSupport, meetsMinimumRequirements, getWebGLErrorMessage } from '../utils/webgl-detect';

// Type checks
const _verifyTypes: {
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  renderer: THREE.WebGLRenderer;
  fbxLoader: FBXLoader;
  gltfLoader: GLTFLoader;
  canvas: typeof Canvas;
  orbitControls: typeof OrbitControls;
  capabilities: ReturnType<typeof detectWebGLSupport>;
  meetsReqs: boolean;
  errorMsg: string | undefined;
} = {
  scene: new THREE.Scene(),
  camera: new THREE.PerspectiveCamera(),
  renderer: new THREE.WebGLRenderer(),
  fbxLoader: new FBXLoader(),
  gltfLoader: new GLTFLoader(),
  canvas: Canvas,
  orbitControls: OrbitControls,
  capabilities: detectWebGLSupport(),
  meetsReqs: meetsMinimumRequirements(),
  errorMsg: getWebGLErrorMessage(detectWebGLSupport())
};

console.log('✓ Three.js setup verification passed - all imports successful');

export { _verifyTypes };


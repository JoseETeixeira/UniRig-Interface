/**
 * Model component for loading and rendering FBX/GLB 3D models
 * Handles automatic centering, scaling, and material setup
 */

import { useEffect, useRef, useState } from 'react';
import { useThree } from '@react-three/fiber';
import { FBXLoader } from 'three/addons/loaders/FBXLoader.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import * as THREE from 'three';

interface ModelProps {
  url: string;
  onLoad?: (model: THREE.Group) => void;
  onError?: (error: Error) => void;
  onProgress?: (progress: number) => void;
  onAnimationsLoaded?: (animations: THREE.AnimationClip[]) => void;
  loadFullQuality?: boolean; // If false, applies simplification strategies
}

/**
 * Load and render a 3D model from FBX or GLB file
 * Automatically centers and scales the model to fit viewport
 */
export function Model({ url, onLoad, onError, onProgress, onAnimationsLoaded, loadFullQuality = true }: ModelProps) {
  const groupRef = useRef<THREE.Group>(null);
  const [model, setModel] = useState<THREE.Group | null>(null);
  const { camera } = useThree();

  useEffect(() => {
    if (!url) return;

    // Determine file format from URL
    const fileExtension = url.split('.').pop()?.toLowerCase();
    let loader: FBXLoader | GLTFLoader;
    
    if (fileExtension === 'fbx') {
      loader = new FBXLoader();
    } else if (fileExtension === 'glb' || fileExtension === 'gltf') {
      loader = new GLTFLoader();
    } else {
      const error = new Error(`Unsupported file format: ${fileExtension}. Supported formats: FBX, GLB, GLTF`);
      onError?.(error);
      return;
    }

    // Track loading progress
    const handleProgress = (event: ProgressEvent) => {
      if (event.lengthComputable) {
        const progress = (event.loaded / event.total) * 100;
        onProgress?.(progress);
      }
    };

    // Load the model
    loader.load(
      url,
      (loadedModel) => {
        let modelGroup: THREE.Group;
        let animations: THREE.AnimationClip[] = [];

        // Extract model and animations based on format
        if (fileExtension === 'fbx') {
          modelGroup = loadedModel as THREE.Group;
          // FBX animations are stored in the model's animations property
          animations = (loadedModel as any).animations || [];
        } else {
          // GLTF format
          const gltf = loadedModel as any;
          modelGroup = gltf.scene;
          animations = gltf.animations || [];
        }

        // Setup materials for proper rendering
        modelGroup.traverse((child) => {
          if ((child as THREE.Mesh).isMesh) {
            const mesh = child as THREE.Mesh;
            
            // Enable shadows
            mesh.castShadow = true;
            mesh.receiveShadow = true;

            // Apply quality optimizations for simplified mode
            if (!loadFullQuality) {
              // Reduce geometry detail for large models
              if (mesh.geometry && mesh.geometry.attributes.position) {
                const vertexCount = mesh.geometry.attributes.position.count;
                // For meshes with >100k vertices, apply simplification hints
                if (vertexCount > 100000) {
                  // Disable expensive rendering features
                  mesh.frustumCulled = true;
                  
                  // Simplify materials
                  if (mesh.material) {
                    const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
                    materials.forEach(mat => {
                      if (mat instanceof THREE.MeshStandardMaterial) {
                        // Reduce material complexity
                        mat.flatShading = true;
                        mat.roughness = 0.8;
                        mat.metalness = 0.2;
                      }
                    });
                  }
                }
              }
            }

            // Ensure materials render correctly
            if (mesh.material) {
              if (Array.isArray(mesh.material)) {
                mesh.material.forEach(mat => {
                  if (mat instanceof THREE.MeshStandardMaterial) {
                    mat.needsUpdate = true;
                  }
                });
              } else if (mesh.material instanceof THREE.MeshStandardMaterial) {
                mesh.material.needsUpdate = true;
              }
            }
          }
        });

        // Calculate bounding box for centering and scaling
        const box = new THREE.Box3().setFromObject(modelGroup);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        
        // Calculate scale to fit model in viewport (target size ~2 units)
        const maxDim = Math.max(size.x, size.y, size.z);
        const targetSize = 2;
        const scale = targetSize / maxDim;

        // Center the model at origin
        modelGroup.position.set(-center.x, -center.y, -center.z);

        // Create a parent group for scaling
        const scaledGroup = new THREE.Group();
        scaledGroup.add(modelGroup);
        scaledGroup.scale.set(scale, scale, scale);

        // Position camera to view the model
        const distance = targetSize * 2;
        camera.position.set(distance, distance * 0.5, distance);
        camera.lookAt(0, 0, 0);

        setModel(scaledGroup);
        onLoad?.(scaledGroup);
        
        // Notify about animations if present
        if (animations.length > 0) {
          onAnimationsLoaded?.(animations);
        }
        
        onProgress?.(100);
      },
      handleProgress,
      (error) => {
        console.error('Error loading model:', error);
        const errorObj = error instanceof Error 
          ? error 
          : new Error(`Failed to load model from ${url}`);
        onError?.(errorObj);
      }
    );

    // Cleanup
    return () => {
      if (model) {
        model.traverse((child) => {
          if ((child as THREE.Mesh).isMesh) {
            const mesh = child as THREE.Mesh;
            mesh.geometry?.dispose();
            if (mesh.material) {
              if (Array.isArray(mesh.material)) {
                mesh.material.forEach(mat => mat.dispose());
              } else {
                mesh.material.dispose();
              }
            }
          }
        });
      }
    };
  }, [url]);

  return model ? <primitive object={model} ref={groupRef} /> : null;
}

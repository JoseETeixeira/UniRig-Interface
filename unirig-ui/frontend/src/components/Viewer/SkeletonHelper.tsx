/**
 * SkeletonHelper Component
 * 
 * Renders a visual overlay of the skeleton/bone structure from a rigged 3D model.
 * Displays bones as lines connecting joints with hover tooltips showing bone names.
 */

import { useEffect, useRef, useState } from 'react';
import { useThree } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import * as THREE from 'three';

interface SkeletonHelperProps {
  model: THREE.Group;
  visible?: boolean;
  color?: string;
  lineWidth?: number;
}

interface BoneInfo {
  name: string;
  position: THREE.Vector3;
}

/**
 * Extract all bones from a model's skeleton
 */
function extractBones(object: THREE.Object3D): THREE.Bone[] {
  const bones: THREE.Bone[] = [];
  
  object.traverse((child) => {
    if (child instanceof THREE.Bone) {
      bones.push(child);
    }
  });
  
  return bones;
}

/**
 * Create line geometry connecting bone joints
 */
function createBoneGeometry(bones: THREE.Bone[]): THREE.BufferGeometry {
  const positions: number[] = [];
  
  bones.forEach((bone) => {
    // Get bone's world position
    const bonePos = new THREE.Vector3();
    bone.getWorldPosition(bonePos);
    
    // If bone has a parent, draw line to parent
    if (bone.parent && bone.parent instanceof THREE.Bone) {
      const parentPos = new THREE.Vector3();
      bone.parent.getWorldPosition(parentPos);
      
      // Add line from parent to bone
      positions.push(parentPos.x, parentPos.y, parentPos.z);
      positions.push(bonePos.x, bonePos.y, bonePos.z);
    }
  });
  
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  
  return geometry;
}

/**
 * Skeleton visualization overlay component
 * Renders bones as lines and provides hover tooltips
 */
export function SkeletonHelper({
  model,
  visible = true,
  color = '#00ff00',
  lineWidth = 2,
}: SkeletonHelperProps) {
  const { scene, gl } = useThree();
  const lineRef = useRef<THREE.LineSegments>(null);
  const [hoveredBone, setHoveredBone] = useState<BoneInfo | null>(null);
  const [bones, setBones] = useState<THREE.Bone[]>([]);
  const raycaster = useRef(new THREE.Raycaster());
  const mouse = useRef(new THREE.Vector2());

  // Extract bones from model
  useEffect(() => {
    if (!model) return;
    
    const extractedBones = extractBones(model);
    setBones(extractedBones);
    
    console.log(`Extracted ${extractedBones.length} bones from model`);
  }, [model]);

  // Create skeleton line geometry
  useEffect(() => {
    if (!lineRef.current || bones.length === 0) return;
    
    const geometry = createBoneGeometry(bones);
    lineRef.current.geometry.dispose();
    lineRef.current.geometry = geometry;
  }, [bones]);

  // Handle mouse move for hover detection
  useEffect(() => {
    if (!visible || bones.length === 0) return;
    
    const handleMouseMove = (event: MouseEvent) => {
      // Calculate mouse position in normalized device coordinates
      const rect = gl.domElement.getBoundingClientRect();
      mouse.current.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.current.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      
      // Update raycaster
      raycaster.current.setFromCamera(mouse.current, scene.getObjectByProperty('isCamera', true) as THREE.Camera);
      
      // Check intersection with bones
      let closestBone: BoneInfo | null = null;
      let closestDistance = Infinity;
      
      bones.forEach((bone) => {
        const bonePos = new THREE.Vector3();
        bone.getWorldPosition(bonePos);
        
        // Create a small sphere around bone for hit detection
        const sphere = new THREE.Sphere(bonePos, 0.1);
        const ray = raycaster.current.ray;
        
        const intersectionPoint = new THREE.Vector3();
        if (ray.intersectSphere(sphere, intersectionPoint)) {
          const distance = intersectionPoint.distanceTo(ray.origin);
          if (distance < closestDistance) {
            closestDistance = distance;
            closestBone = {
              name: bone.name || 'Unnamed Bone',
              position: bonePos.clone(),
            };
          }
        }
      });
      
      setHoveredBone(closestBone);
    };
    
    gl.domElement.addEventListener('mousemove', handleMouseMove);
    
    return () => {
      gl.domElement.removeEventListener('mousemove', handleMouseMove);
    };
  }, [visible, bones, scene, gl]);

  if (!visible || bones.length === 0) {
    return null;
  }

  return (
    <>
      {/* Skeleton lines */}
      <lineSegments ref={lineRef}>
        <bufferGeometry />
        <lineBasicMaterial
          color={color}
          linewidth={lineWidth}
          transparent
          opacity={0.8}
          depthTest={false}
        />
      </lineSegments>
      
      {/* Bone joint spheres for better visibility */}
      {bones.map((bone, index) => {
        const pos = new THREE.Vector3();
        bone.getWorldPosition(pos);
        
        return (
          <mesh key={index} position={pos}>
            <sphereGeometry args={[0.02, 8, 8]} />
            <meshBasicMaterial
              color={color}
              transparent
              opacity={0.8}
              depthTest={false}
            />
          </mesh>
        );
      })}
      
      {/* Hover tooltip */}
      {hoveredBone && (
        <Html position={hoveredBone.position}>
          <div className="bg-gray-900 text-white px-2 py-1 rounded text-xs whitespace-nowrap pointer-events-none">
            {hoveredBone.name}
          </div>
        </Html>
      )}
    </>
  );
}

/**
 * 3D viewer component using Three.js.
 * Displays the mesh geometry from the backend.
 */

import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import type { MeshData } from '../types/ir';

interface Viewer3DProps {
  mesh: MeshData | null;
  selectedFeatureId?: string | null;
  onFeatureSelect?: (featureId: string | null) => void;
}

export function Viewer3D({ mesh, selectedFeatureId, onFeatureSelect }: Viewer3DProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const meshRef = useRef<THREE.Mesh | null>(null);
  const meshesByFeatureRef = useRef<Map<string, THREE.Mesh>>(new Map());

  useEffect(() => {
    if (!containerRef.current) return;

    // Initialize scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a1a);
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(
      75,
      containerRef.current.clientWidth / containerRef.current.clientHeight,
      0.1,
      1000
    );
    camera.position.set(50, 50, 50);
    camera.lookAt(0, 0, 0);
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(50, 50, 50);
    scene.add(directionalLight);

    // Grid helper
    const gridHelper = new THREE.GridHelper(100, 10);
    scene.add(gridHelper);

    // Orbit controls (simple implementation)
    let isDragging = false;
    let previousMousePosition = { x: 0, y: 0 };

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      previousMousePosition = { x: e.clientX, y: e.clientY };
    };

    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;

      const deltaX = e.clientX - previousMousePosition.x;
      const deltaY = e.clientY - previousMousePosition.y;

      // Rotate camera around the origin
      const spherical = new THREE.Spherical();
      spherical.setFromVector3(camera.position);
      spherical.theta -= deltaX * 0.01;
      spherical.phi += deltaY * 0.01;
      spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.phi));

      camera.position.setFromSpherical(spherical);
      camera.lookAt(0, 0, 0);

      previousMousePosition = { x: e.clientX, y: e.clientY };
    };

    const onMouseUp = () => {
      isDragging = false;
    };

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const scale = e.deltaY > 0 ? 1.1 : 0.9;
      camera.position.multiplyScalar(scale);
    };

    // Store onFeatureSelect in a ref so it's accessible in closures
    const onFeatureSelectRef = { current: onFeatureSelect };
    
    renderer.domElement.addEventListener('mousedown', onMouseDown);
    renderer.domElement.addEventListener('mousemove', onMouseMove);
    renderer.domElement.addEventListener('mouseup', onMouseUp);
    renderer.domElement.addEventListener('wheel', onWheel);

    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };
    animate();

    // Update onFeatureSelect ref when prop changes
    onFeatureSelectRef.current = onFeatureSelect;
    
    // Cleanup
    return () => {
      renderer.domElement.removeEventListener('mousedown', onMouseDown);
      renderer.domElement.removeEventListener('mousemove', onMouseMove);
      renderer.domElement.removeEventListener('mouseup', onMouseUp);
      renderer.domElement.removeEventListener('wheel', onWheel);
      if (containerRef.current && renderer.domElement.parentNode) {
        containerRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [onFeatureSelect]);

  // Update mesh when it changes
  useEffect(() => {
    if (!mesh || !sceneRef.current) return;
    
    // Check if mesh has valid data
    if (!mesh.vertices || mesh.vertices.length === 0 || !mesh.faces || mesh.faces.length === 0) {
      return;
    }

    // Remove old meshes
    meshesByFeatureRef.current.forEach((oldMesh) => {
      sceneRef.current?.remove(oldMesh);
      oldMesh.geometry.dispose();
      if (Array.isArray(oldMesh.material)) {
        oldMesh.material.forEach(m => m.dispose());
      } else {
        oldMesh.material.dispose();
      }
    });
    meshesByFeatureRef.current.clear();

    if (meshRef.current) {
      sceneRef.current.remove(meshRef.current);
      meshRef.current.geometry.dispose();
      if (Array.isArray(meshRef.current.material)) {
        meshRef.current.material.forEach(m => m.dispose());
      } else {
        meshRef.current.material.dispose();
      }
      meshRef.current = null;
    }

    // Check if we have per-feature mesh data
    const meshWithFeatures = mesh as MeshData & { faceToFeature?: (string | null)[] };
    if (meshWithFeatures.faceToFeature && meshWithFeatures.faceToFeature.length > 0) {
      // Simple approach: create one combined mesh but track selection via faceToFeature
      // For MVP, we'll create a single mesh but use faceToFeature for selection
      const vertices = new Float32Array(mesh.vertices.flat());
      const indices = Array.from(new Uint32Array(mesh.faces.flat()));

      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
      geometry.setIndex(indices);
      geometry.computeVertexNormals();
      
      // Store faceToFeature mapping in geometry userData
      geometry.userData.faceToFeature = meshWithFeatures.faceToFeature;

      const material = new THREE.MeshStandardMaterial({
        color: 0x4a90e2,
        metalness: 0.3,
        roughness: 0.7,
      });

      const threeMesh = new THREE.Mesh(geometry, material);
      // Extract unique features from faceToFeature
      const featureSet = new Set<string>();
      meshWithFeatures.faceToFeature.forEach((f: string | null | undefined) => {
        if (f) featureSet.add(f);
      });
      threeMesh.userData.allFeatures = Array.from(featureSet);
      sceneRef.current.add(threeMesh);
      meshRef.current = threeMesh;
    } else {
      // Single mesh (legacy behavior)
      const vertices = new Float32Array(mesh.vertices.flat());
      const indices = Array.from(new Uint32Array(mesh.faces.flat()));

      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
      geometry.setIndex(indices);
      geometry.computeVertexNormals();

      const material = new THREE.MeshStandardMaterial({
        color: 0x4a90e2,
        metalness: 0.3,
        roughness: 0.7,
      });

      const threeMesh = new THREE.Mesh(geometry, material);
      const meshWithId = mesh as MeshData & { featureId?: string };
      if (meshWithId.featureId) {
        threeMesh.userData.featureId = meshWithId.featureId;
        meshesByFeatureRef.current.set(meshWithId.featureId, threeMesh);
      }
      sceneRef.current.add(threeMesh);
      meshRef.current = threeMesh;
    }

    // Center and scale camera
    if (cameraRef.current && sceneRef.current && meshRef.current) {
      const geometry = meshRef.current.geometry;
      geometry.computeBoundingBox();
      const box = geometry.boundingBox;
      if (box) {
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        cameraRef.current.position.set(
          center.x + maxDim,
          center.y + maxDim,
          center.z + maxDim
        );
        cameraRef.current.lookAt(center);
      }
    }
  }, [mesh]);

  // Update selection highlighting
  useEffect(() => {
    if (!sceneRef.current) return;
    
    // Update material colors based on selection
    meshesByFeatureRef.current.forEach((mesh, featureId) => {
      if (mesh.material instanceof THREE.MeshStandardMaterial) {
        mesh.material.color.setHex(selectedFeatureId === featureId ? 0xff6b6b : 0x4a90e2);
        mesh.material.emissive.setHex(selectedFeatureId === featureId ? 0x330000 : 0x000000);
      }
    });
    
    // Also handle single mesh case
    if (meshRef.current && meshRef.current.material instanceof THREE.MeshStandardMaterial) {
      const isSelected = meshRef.current.userData.featureId === selectedFeatureId ||
                        (meshRef.current.userData.allFeatures && 
                         Array.isArray(meshRef.current.userData.allFeatures) &&
                         meshRef.current.userData.allFeatures.includes(selectedFeatureId));
      meshRef.current.material.color.setHex(isSelected ? 0xff6b6b : 0x4a90e2);
      meshRef.current.material.emissive.setHex(isSelected ? 0x330000 : 0x000000);
    }
  }, [selectedFeatureId]);

  // Handle resize
  useEffect(() => {
    const handleResize = () => {
      if (!containerRef.current || !cameraRef.current || !rendererRef.current) return;
      cameraRef.current.aspect = containerRef.current.clientWidth / containerRef.current.clientHeight;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
      }}
    />
  );
}


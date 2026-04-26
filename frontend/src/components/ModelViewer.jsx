import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Environment, Center, useGLTF } from "@react-three/drei";

function Body({ url }) {
  const { scene } = useGLTF(url);
  return (
    <Center>
      <primitive object={scene} />
    </Center>
  );
}

export default function ModelViewer({ meshUrl }) {
  return (
    <div className="viewer">
      <Canvas camera={{ position: [0, 1.0, 3.0], fov: 35 }}>
        <ambientLight intensity={0.6} />
        <directionalLight position={[3, 5, 2]} intensity={0.9} />
        <directionalLight position={[-3, 2, -2]} intensity={0.4} />
        <Suspense fallback={null}>
          {meshUrl ? <Body url={meshUrl} /> : null}
          <Environment preset="city" />
        </Suspense>
        <OrbitControls makeDefault target={[0, 0, 0]} />
        <gridHelper args={[6, 12, "#2a2f3d", "#1a1d27"]} position={[0, -0.001, 0]} />
      </Canvas>
      {!meshUrl && (
        <div className="status">
          Fill in the panel and click <b>Generate 3D body</b> to build a mesh.
        </div>
      )}
    </div>
  );
}

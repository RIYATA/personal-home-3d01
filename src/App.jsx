import React, { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Line, Sparkles, Stars, useGLTF } from "@react-three/drei";
import * as THREE from "three";

const modelUrl = (filename) => `${import.meta.env.BASE_URL}models/${filename}`;
const MODEL_URLS = {
  environment: modelUrl("environment.glb"),
  meadow: modelUrl("meadow.glb"),
  climber: modelUrl("climber.glb"),
  cableCar: modelUrl("cable-car.glb"),
  sheep: modelUrl("sheep.glb"),
  camp: modelUrl("camp.glb"),
};

const ROUTE_POINTS = [
  new THREE.Vector3(-5.8, -1.1, 0.4),
  new THREE.Vector3(-4.4, 0.15, -0.55),
  new THREE.Vector3(-3.1, 1.25, -0.95),
  new THREE.Vector3(-1.85, 2.25, -0.72),
  new THREE.Vector3(-0.72, 3.4, -0.95),
  new THREE.Vector3(0.25, 4.72, -0.5),
];

const CABLE_POINTS = [
  new THREE.Vector3(0.25, 4.72, -0.5),
  new THREE.Vector3(1.8, 4.98, -1.35),
  new THREE.Vector3(3.55, 4.1, -2.15),
  new THREE.Vector3(4.82, 3.08, -2.92),
];

const MEADOW_CENTER = new THREE.Vector3(5.05, 2.36, -1.3);
const MEADOW_SPAWN = new THREE.Vector2(-0.92, 0.42);
const SHEEP_OFFSET = new THREE.Vector2(0.36, 0.02);
const SHEEP_POS = MEADOW_CENTER.clone().add(new THREE.Vector3(SHEEP_OFFSET.x, 0.26, SHEEP_OFFSET.y));
const CAMP_POS = new THREE.Vector3(4.7, -1.08, 3.4);
const ZERO = new THREE.Vector3();
const UP = new THREE.Vector3(0, 1, 0);

const CHAPTERS = [
  { id: "base", index: "01", label: "雪线", phase: "climb", progress: 0 },
  { id: "summit", index: "02", label: "山顶", phase: "climb", progress: 1 },
  { id: "cable", index: "03", label: "缆车", phase: "cable", progress: 1 },
  { id: "meadow", index: "04", label: "牧场", phase: "meadow", progress: 1 },
  { id: "camp", index: "05", label: "星火", phase: "camp", progress: 1 },
];

const SCENES = {
  climb: {
    kicker: "第一幕 · 雪线",
    title: "沿星绳向山顶攀登",
    detail: "方向键控制巫师女孩。沿着发光节点向上，抵达山顶缆车站。",
  },
  summit: {
    kicker: "第二幕 · 山顶站",
    title: "风停在缆车之前",
    detail: "已经到达山顶。靠近吊索，准备越过山脊。",
  },
  cable: {
    kicker: "第三幕 · 越岭",
    title: "乘缆车穿过云层",
    detail: "缆车会自动前行，镜头跟随穿过雪峰，前往另一侧的牧场。",
  },
  meadow: {
    kicker: "第四幕 · 月光牧场",
    title: "找到山羊并递出青草",
    detail: "在火山口草地内自由移动。走近羊后，互动提示才会亮起。",
  },
  fed: {
    kicker: "牧场任务完成",
    title: "羊已经吃饱了",
    detail: "短暂的停留结束。继续前往夜色中的星火营地。",
  },
  camp: {
    kicker: "终幕 · 星火",
    title: "在篝火旁看一夜星星",
    detail: "旅程在这里安静下来。这里将承载联系方式和你的个人结语。",
  },
};

const KEY_LABELS = {
  climb: ["↑ ↓", "攀登"],
  summit: ["E", "乘缆车"],
  cable: ["自动", "越岭中"],
  meadow: ["方向键", "寻找羊"],
  feed: ["E", "喂草"],
  fed: ["E", "前往营地"],
  camp: ["完成", "旅程结束"],
};

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function useKeyboard() {
  const keys = useRef({
    ArrowUp: false,
    ArrowDown: false,
    ArrowLeft: false,
    ArrowRight: false,
  });

  useEffect(() => {
    const tracked = new Set(Object.keys(keys.current));
    const onKeyDown = (event) => {
      if (!tracked.has(event.key)) return;
      keys.current[event.key] = true;
      event.preventDefault();
    };
    const onKeyUp = (event) => {
      if (!tracked.has(event.key)) return;
      keys.current[event.key] = false;
      event.preventDefault();
    };
    const clear = () => {
      Object.keys(keys.current).forEach((key) => {
        keys.current[key] = false;
      });
    };

    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("keyup", onKeyUp);
    window.addEventListener("blur", clear);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("keyup", onKeyUp);
      window.removeEventListener("blur", clear);
    };
  }, []);

  return keys;
}

function App() {
  const [phase, setPhase] = useState("climb");
  const [hud, setHud] = useState({
    scene: SCENES.climb,
    chapter: "base",
    progress: 0,
    prompt: KEY_LABELS.climb,
    canAct: false,
  });
  const [checkpointRequest, setCheckpointRequest] = useState({ id: "base", token: 0 });

  const goToCheckpoint = (id) => {
    setCheckpointRequest((current) => ({ id, token: current.token + 1 }));
  };

  return (
    <main className={`game-shell phase-${phase}`}>
      <Canvas
        camera={{ position: [-8.2, 4.8, 9.8], fov: 48 }}
        dpr={[1, 1.75]}
        gl={{ antialias: true, powerPreference: "high-performance" }}
        shadows
      >
        <Suspense fallback={null}>
          <AdventureScene
            phase={phase}
            setPhase={setPhase}
            setHud={setHud}
            checkpointRequest={checkpointRequest}
          />
        </Suspense>
      </Canvas>

      <header className="game-header">
        <div className="game-brand">
          <span className="moon-mark" aria-hidden="true" />
          <div>
            <p>Moontrail</p>
            <strong>巫师女孩的雪山旅程</strong>
          </div>
        </div>

        <nav className="profile-nav" aria-label="个人主页栏目">
          <a href="#works">作品</a>
          <a href="#about">关于</a>
          <a href="#story">经历</a>
          <a href="#contact">联系</a>
        </nav>

        <button
          className="icon-button reset-button"
          type="button"
          title="重新开始"
          aria-label="重新开始"
          onClick={() => goToCheckpoint("base")}
        >
          ↺
        </button>
      </header>

      <section className="scene-copy" aria-live="polite">
        <span>{hud.scene.kicker}</span>
        <h1>{hud.scene.title}</h1>
        <p>{hud.scene.detail}</p>
        <div className="journey-progress" aria-label="旅程进度">
          <i style={{ width: `${Math.round(hud.progress * 100)}%` }} />
        </div>
      </section>

      <div className={`action-prompt ${hud.canAct ? "is-ready" : ""}`}>
        <kbd>{hud.prompt[0]}</kbd>
        <span>{hud.prompt[1]}</span>
      </div>

      <ChapterRail
        activeId={hud.chapter}
        progress={hud.progress}
        onSelect={goToCheckpoint}
      />

      <MobileControls />
    </main>
  );
}

function ChapterRail({ activeId, progress, onSelect }) {
  return (
    <nav className="chapter-rail" aria-label="旅程章节">
      <span className="chapter-line" aria-hidden="true">
        <i style={{ width: `${Math.round(progress * 100)}%` }} />
      </span>
      {CHAPTERS.map((chapter) => {
        const isActive = chapter.id === activeId;
        const isComplete = CHAPTERS.findIndex((item) => item.id === activeId) > CHAPTERS.indexOf(chapter);
        return (
          <button
            key={chapter.id}
            type="button"
            className={`chapter-button ${isActive ? "is-active" : ""} ${isComplete ? "is-complete" : ""}`}
            title={`前往${chapter.label}`}
            aria-current={isActive ? "step" : undefined}
            onClick={() => onSelect(chapter.id)}
          >
            <span className="chapter-icon" data-icon-slot={chapter.id} aria-hidden="true">
              {chapter.index}
            </span>
            <strong>{chapter.label}</strong>
          </button>
        );
      })}
    </nav>
  );
}

function MobileControls() {
  const sendKey = (type, key) => {
    window.dispatchEvent(new KeyboardEvent(type, { key, bubbles: true }));
  };
  const holdHandlers = (key) => ({
    onPointerDown: (event) => {
      event.currentTarget.setPointerCapture(event.pointerId);
      sendKey("keydown", key);
    },
    onPointerUp: () => sendKey("keyup", key),
    onPointerCancel: () => sendKey("keyup", key),
  });
  const action = () => {
    sendKey("keydown", "Enter");
    sendKey("keyup", "Enter");
  };

  return (
    <div className="mobile-controls" aria-label="触控游戏控制">
      <button className="control-up" type="button" aria-label="向上" {...holdHandlers("ArrowUp")}>↑</button>
      <button className="control-left" type="button" aria-label="向左" {...holdHandlers("ArrowLeft")}>←</button>
      <button className="control-action" type="button" aria-label="互动" onClick={action}>E</button>
      <button className="control-right" type="button" aria-label="向右" {...holdHandlers("ArrowRight")}>→</button>
      <button className="control-down" type="button" aria-label="向下" {...holdHandlers("ArrowDown")}>↓</button>
    </div>
  );
}

function AdventureScene({ phase, setPhase, setHud, checkpointRequest }) {
  const keys = useKeyboard();
  const route = useMemo(() => new THREE.CatmullRomCurve3(ROUTE_POINTS), []);
  const cable = useMemo(() => new THREE.CatmullRomCurve3(CABLE_POINTS), []);
  const routeLine = useMemo(() => route.getPoints(72), [route]);
  const cableLine = useMemo(() => cable.getPoints(56), [cable]);
  const phaseRef = useRef(phase);
  const climbProgress = useRef(0);
  const cableProgress = useRef(0);
  const lateralOffset = useRef(0);
  const meadowOffset = useRef(MEADOW_SPAWN.clone());
  const fedRef = useRef(false);
  const nearSheepRef = useRef(false);
  const climberRef = useRef(null);
  const cableCarRef = useRef(null);
  const sheepRef = useRef(null);
  const fireRef = useRef(null);
  const lastHudSignature = useRef("");
  const lastHudUpdate = useRef(0);
  const [fed, setFed] = useState(false);
  const { camera } = useThree();

  useEffect(() => {
    phaseRef.current = phase;
  }, [phase]);

  useEffect(() => {
    const onAction = (event) => {
      if (!["Enter", " ", "e", "E"].includes(event.key)) return;
      event.preventDefault();

      if (phaseRef.current === "climb" && climbProgress.current >= 0.965) {
        cableProgress.current = 0;
        phaseRef.current = "cable";
        setPhase("cable");
        return;
      }

      if (phaseRef.current === "meadow" && !fedRef.current && nearSheepRef.current) {
        fedRef.current = true;
        setFed(true);
        return;
      }

      if (phaseRef.current === "meadow" && fedRef.current) {
        phaseRef.current = "camp";
        setPhase("camp");
      }
    };

    window.addEventListener("keydown", onAction);
    return () => window.removeEventListener("keydown", onAction);
  }, [setPhase]);

  useEffect(() => {
    if (checkpointRequest.token === 0) return;
    const checkpoint = CHAPTERS.find((item) => item.id === checkpointRequest.id);
    if (!checkpoint) return;

    Object.keys(keys.current).forEach((key) => {
      keys.current[key] = false;
    });
    climbProgress.current = checkpoint.progress;
    cableProgress.current = checkpoint.id === "meadow" ? 1 : 0;
    lateralOffset.current = 0;
    meadowOffset.current.copy(MEADOW_SPAWN);
    fedRef.current = false;
    nearSheepRef.current = false;
    setFed(false);
    phaseRef.current = checkpoint.phase;
    setPhase(checkpoint.phase);
    lastHudSignature.current = "";

    if (climberRef.current) {
      climberRef.current.visible = checkpoint.phase !== "cable";
      resetCharacterPose(climberRef.current);
    }

    const routePoint = route.getPoint(climbProgress.current);
    const cablePoint = cable.getPoint(cableProgress.current);
    const meadowPoint = getMeadowPlayerPoint();
    const target = getCameraTarget(checkpoint.phase, routePoint, cablePoint, meadowPoint);
    camera.position.copy(getCameraPosition(checkpoint.phase, target));
    camera.lookAt(target);
  }, [camera, cable, checkpointRequest, keys, route, setPhase]);

  useFrame((state, delta) => {
    const activePhase = phaseRef.current;
    const elapsed = state.clock.elapsedTime;
    let routePoint = route.getPoint(climbProgress.current);
    let cablePoint = cable.getPoint(cableProgress.current);
    let meadowPoint = getMeadowPlayerPoint();

    if (activePhase === "climb") {
      const forward = (keys.current.ArrowUp ? 1 : 0) - (keys.current.ArrowDown ? 1 : 0);
      const side = (keys.current.ArrowRight ? 1 : 0) - (keys.current.ArrowLeft ? 1 : 0);
      climbProgress.current = clamp(climbProgress.current + forward * delta * 0.14, 0, 1);
      lateralOffset.current = clamp(lateralOffset.current + side * delta * 0.58, -0.28, 0.28);

      const currentPoint = route.getPoint(climbProgress.current);
      const tangent = route.getTangent(climbProgress.current);
      const sideways = new THREE.Vector3(-tangent.z, 0, tangent.x)
        .normalize()
        .multiplyScalar(lateralOffset.current);
      currentPoint.add(sideways);
      routePoint = currentPoint;
      placeCharacter(climberRef.current, currentPoint, tangent, elapsed, Math.abs(forward) + Math.abs(side));
    }

    if (activePhase === "cable") {
      cableProgress.current = clamp(cableProgress.current + delta * 0.105, 0, 1);
      cablePoint = cable.getPoint(cableProgress.current);
      const tangent = cable.getTangent(cableProgress.current);
      if (cableCarRef.current) {
        cableCarRef.current.visible = true;
        cableCarRef.current.position.copy(cablePoint);
        cableCarRef.current.rotation.y = Math.atan2(tangent.x, tangent.z);
        cableCarRef.current.rotation.z = Math.sin(elapsed * 2.8) * 0.025;
      }
      if (climberRef.current) climberRef.current.visible = false;

      if (cableProgress.current >= 0.998) {
        phaseRef.current = "meadow";
        setPhase("meadow");
        meadowOffset.current.copy(MEADOW_SPAWN);
      }
    } else if (cableCarRef.current) {
      cableCarRef.current.visible = false;
    }

    if (activePhase === "meadow") {
      const movement = new THREE.Vector2(
        (keys.current.ArrowRight ? 1 : 0) - (keys.current.ArrowLeft ? 1 : 0),
        (keys.current.ArrowDown ? 1 : 0) - (keys.current.ArrowUp ? 1 : 0),
      );
      if (movement.lengthSq() > 0) {
        movement.normalize();
        meadowOffset.current.addScaledVector(movement, delta * 0.72);
        const radius = meadowOffset.current.length();
        if (radius > 1.02) meadowOffset.current.multiplyScalar(1.02 / radius);
      }

      meadowPoint = getMeadowPlayerPoint();
      const facing = movement.lengthSq() > 0
        ? new THREE.Vector3(movement.x, 0, movement.y)
        : ZERO;
      placeCharacter(climberRef.current, meadowPoint, facing, elapsed, movement.length());
      if (climberRef.current) climberRef.current.visible = true;

      nearSheepRef.current = meadowOffset.current.distanceTo(SHEEP_OFFSET) < 0.62;
      animateSheep(sheepRef.current, elapsed, fedRef.current);
      if (fedRef.current) poseFeeding(climberRef.current, elapsed);
    }

    if (activePhase === "camp") {
      const restPoint = CAMP_POS.clone().add(new THREE.Vector3(-0.68, -0.05, 0.14));
      placeCharacter(climberRef.current, restPoint, ZERO, elapsed, 0);
      poseSleeping(climberRef.current);
      if (climberRef.current) climberRef.current.visible = true;
      if (fireRef.current) {
        const pulse = 0.92 + Math.sin(elapsed * 7.2) * 0.12;
        fireRef.current.scale.setScalar(pulse);
      }
    }

    const target = getCameraTarget(activePhase, routePoint, cablePoint, meadowPoint);
    const desiredCamera = getCameraPosition(activePhase, target);
    camera.position.lerp(desiredCamera, 1 - Math.pow(0.002, delta));
    camera.lookAt(target);

    if (elapsed - lastHudUpdate.current > 0.1) {
      lastHudUpdate.current = elapsed;
      const nextHud = getHudState(
        activePhase,
        climbProgress.current,
        cableProgress.current,
        nearSheepRef.current,
        fedRef.current,
      );
      const signature = JSON.stringify(nextHud);
      if (signature !== lastHudSignature.current) {
        lastHudSignature.current = signature;
        setHud(nextHud);
      }
    }
  });

  const night = phase === "camp";
  return (
    <>
      <color attach="background" args={[night ? "#03091d" : "#173a62"]} />
      <fog attach="fog" args={[night ? "#03091d" : "#173a62", night ? 10 : 9, night ? 28 : 25]} />
      <ambientLight intensity={night ? 0.26 : 0.8} />
      <hemisphereLight args={[night ? "#304b86" : "#bdeaff", "#15223b", night ? 0.34 : 0.72]} />
      <directionalLight
        position={[-7, 10, 5]}
        intensity={night ? 0.28 : 1.45}
        castShadow
        shadow-mapSize={[1024, 1024]}
      />
      <Stars
        radius={54}
        depth={26}
        count={night ? 1200 : 260}
        factor={night ? 4.2 : 2}
        saturation={0.2}
        fade
        speed={0.3}
      />
      {phase === "meadow" ? (
        <Sparkles position={MEADOW_CENTER} count={32} scale={[3.4, 1.8, 3.4]} size={2} speed={0.25} color="#fff3a8" />
      ) : null}

      {phase !== "camp" ? <SnowField /> : null}
      <MountainWorld routeLine={routeLine} cableLine={cableLine} phase={phase} />
      <CableCar ref={cableCarRef} />
      <Climber ref={climberRef} />
      <Sheep ref={sheepRef} position={SHEEP_POS} feeding={fed} />
      <Campfire ref={fireRef} active={phase === "camp"} />
      <InteractionMarker
        visible={phase === "climb" && climbProgress.current >= 0.93}
        position={ROUTE_POINTS[ROUTE_POINTS.length - 1].clone().add(new THREE.Vector3(0, 0.85, 0))}
        color="#f8dc72"
      />
      <InteractionMarker
        visible={phase === "meadow" && !fed}
        position={SHEEP_POS.clone().add(new THREE.Vector3(0, 0.92, 0))}
        color="#9cf58d"
      />
    </>
  );

  function getMeadowPlayerPoint() {
    return MEADOW_CENTER.clone().add(new THREE.Vector3(
      meadowOffset.current.x,
      0.14,
      meadowOffset.current.y,
    ));
  }
}

function getHudState(phase, climb, cable, nearSheep, fed) {
  if (phase === "climb") {
    const summit = climb >= 0.965;
    return {
      scene: summit ? SCENES.summit : SCENES.climb,
      chapter: summit ? "summit" : "base",
      progress: 0.2 * climb,
      prompt: summit ? KEY_LABELS.summit : KEY_LABELS.climb,
      canAct: summit,
    };
  }
  if (phase === "cable") {
    return {
      scene: SCENES.cable,
      chapter: "cable",
      progress: 0.4 + cable * 0.2,
      prompt: KEY_LABELS.cable,
      canAct: false,
    };
  }
  if (phase === "meadow") {
    return {
      scene: fed ? SCENES.fed : SCENES.meadow,
      chapter: "meadow",
      progress: fed ? 0.8 : 0.65,
      prompt: fed ? KEY_LABELS.fed : nearSheep ? KEY_LABELS.feed : KEY_LABELS.meadow,
      canAct: fed || nearSheep,
    };
  }
  return {
    scene: SCENES.camp,
    chapter: "camp",
    progress: 1,
    prompt: KEY_LABELS.camp,
    canAct: false,
  };
}

function resetCharacterPose(group) {
  if (!group) return;
  group.rotation.set(0, 0, 0);
  ["leftLeg", "rightLeg", "leftArm", "rightArm"].forEach((key) => {
    group.userData[key]?.rotation.set(0, 0, 0);
  });
}

function placeCharacter(group, point, tangent, elapsed, pace) {
  if (!group) return;
  resetCharacterPose(group);
  group.position.copy(point);
  group.position.y += 0.15 + Math.sin(elapsed * 8) * 0.025 * pace;
  if (tangent.lengthSq() > 0.001) {
    group.rotation.y = Math.atan2(tangent.x, tangent.z);
  }

  const swing = Math.sin(elapsed * 9.2) * 0.34 * Math.min(1, pace);
  group.userData.leftLeg?.rotation.set(swing, 0, 0);
  group.userData.rightLeg?.rotation.set(-swing, 0, 0);
  group.userData.leftArm?.rotation.set(-swing, 0, 0);
  group.userData.rightArm?.rotation.set(swing, 0, 0);
}

function poseFeeding(group, elapsed) {
  if (!group) return;
  const reach = Math.sin(elapsed * 5.2) * 0.06;
  group.userData.leftArm?.rotation.set(-0.62 + reach, 0, 0.2);
  group.userData.rightArm?.rotation.set(-0.9 - reach, 0, -0.24);
}

function poseSleeping(group) {
  if (!group) return;
  group.rotation.set(0, 0.58, -1.44);
  group.userData.leftArm?.rotation.set(1.1, 0.08, -0.48);
  group.userData.rightArm?.rotation.set(1.24, -0.08, 0.42);
  group.userData.leftLeg?.rotation.set(-0.24, 0, -0.16);
  group.userData.rightLeg?.rotation.set(0.16, 0, 0.12);
}

function animateSheep(group, elapsed, feeding) {
  if (!group) return;
  group.rotation.y = -0.55;
  const head = group.userData.head;
  const grass = group.userData.grass;
  if (head) head.rotation.x = feeding ? 0.48 + Math.sin(elapsed * 5.4) * 0.18 : 0.08;
  if (grass) grass.visible = feeding;
}

function getCameraTarget(phase, routePoint, cablePoint, meadowPoint) {
  if (phase === "cable") return cablePoint.clone().add(new THREE.Vector3(0, 0.12, 0));
  if (phase === "meadow") return meadowPoint.clone().lerp(MEADOW_CENTER, 0.52).add(new THREE.Vector3(0, 0.24, 0));
  if (phase === "camp") return CAMP_POS.clone().add(new THREE.Vector3(-0.15, 0.32, 0));
  return routePoint.clone().lerp(new THREE.Vector3(-2.05, 2.05, -1.05), 0.34).add(new THREE.Vector3(0, 0.58, 0));
}

function getCameraPosition(phase, target) {
  if (phase === "cable") return target.clone().add(new THREE.Vector3(-3.4, 2.1, 5.1));
  if (phase === "meadow") return target.clone().add(new THREE.Vector3(-3.9, 3.65, 4.9));
  if (phase === "camp") return target.clone().add(new THREE.Vector3(-3.5, 2.35, 5.9));
  return target.clone().add(new THREE.Vector3(-5.9, 3.8, 8.1));
}

function prepareModel(model) {
  model.traverse((object) => {
    if (!object.isMesh) return;
    object.castShadow = true;
    object.receiveShadow = true;
    const materials = Array.isArray(object.material) ? object.material : [object.material];
    materials.filter(Boolean).forEach((material) => {
      material.flatShading = true;
      material.needsUpdate = true;
    });
  });
}

function GlbModel({ url, visible = true }) {
  const { scene } = useGLTF(url);
  const model = useMemo(() => scene.clone(true), [scene]);
  useEffect(() => prepareModel(model), [model]);
  return <primitive object={model} visible={visible} />;
}

function MountainWorld({ routeLine, cableLine, phase }) {
  const camp = phase === "camp";
  return (
    <group>
      <GlbModel url={MODEL_URLS.environment} />
      <GlbModel url={MODEL_URLS.meadow} visible={!camp} />
      {!camp ? (
        <>
          <Line points={routeLine} color="#f3e6bf" lineWidth={2.5} transparent opacity={0.62} />
          <Line points={cableLine} color="#f2fbff" lineWidth={2} transparent opacity={0.76} />
        </>
      ) : null}
    </group>
  );
}

function InteractionMarker({ visible, position, color }) {
  const ref = useRef(null);
  useFrame((state) => {
    if (!ref.current) return;
    ref.current.position.y = position.y + Math.sin(state.clock.elapsedTime * 2.8) * 0.08;
    ref.current.rotation.y += 0.02;
  });
  return (
    <group ref={ref} position={position} visible={visible}>
      <mesh rotation={[Math.PI / 4, 0, Math.PI / 4]}>
        <octahedronGeometry args={[0.13, 0]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.8} roughness={0.4} />
      </mesh>
      <pointLight color={color} intensity={1.2} distance={1.7} />
    </group>
  );
}

const Climber = React.forwardRef(function Climber(_, ref) {
  const { scene } = useGLTF(MODEL_URLS.climber);
  const model = useMemo(() => scene.clone(true), [scene]);

  useEffect(() => {
    if (!ref.current) return;
    prepareModel(model);
    ref.current.userData.leftLeg = model.getObjectByName("ANIM_LeftLeg");
    ref.current.userData.rightLeg = model.getObjectByName("ANIM_RightLeg");
    ref.current.userData.leftArm = model.getObjectByName("ANIM_LeftArm");
    ref.current.userData.rightArm = model.getObjectByName("ANIM_RightArm");
  }, [model, ref]);

  return (
    <group ref={ref} scale={0.36}>
      <primitive object={model} />
    </group>
  );
});

const CableCar = React.forwardRef(function CableCar(_, ref) {
  const { scene } = useGLTF(MODEL_URLS.cableCar);
  const model = useMemo(() => scene.clone(true), [scene]);
  useEffect(() => prepareModel(model), [model]);
  return (
    <group ref={ref} visible={false} scale={0.92}>
      <primitive object={model} />
    </group>
  );
});

const Sheep = React.forwardRef(function Sheep({ position, feeding }, ref) {
  const { scene } = useGLTF(MODEL_URLS.sheep);
  const model = useMemo(() => scene.clone(true), [scene]);

  useEffect(() => {
    if (!ref.current) return;
    prepareModel(model);
    ref.current.userData.head = model.getObjectByName("ANIM_Head");
    ref.current.userData.grass = model.getObjectByName("ANIM_GrassBunch");
  }, [model, ref]);

  useEffect(() => {
    const grass = model.getObjectByName("ANIM_GrassBunch");
    if (grass) grass.visible = feeding;
  }, [feeding, model]);

  return (
    <group ref={ref} position={position} scale={0.62}>
      <primitive object={model} />
    </group>
  );
});

const Campfire = React.forwardRef(function Campfire({ active }, ref) {
  const { scene } = useGLTF(MODEL_URLS.camp);
  const model = useMemo(() => scene.clone(true), [scene]);

  useEffect(() => {
    prepareModel(model);
    if (ref && typeof ref === "object") {
      ref.current = model.getObjectByName("ANIM_FlameGroup");
    }
  }, [model, ref]);

  return (
    <group visible={active}>
      <primitive object={model} />
      <pointLight position={CAMP_POS} color="#ffb45c" intensity={4.2} distance={5.5} />
    </group>
  );
});

function SnowField() {
  const points = useMemo(() => {
    const positions = new Float32Array(360 * 3);
    for (let index = 0; index < 360; index += 1) {
      positions[index * 3] = (Math.random() - 0.5) * 28;
      positions[index * 3 + 1] = Math.random() * 10 - 0.2;
      positions[index * 3 + 2] = (Math.random() - 0.5) * 22;
    }
    return positions;
  }, []);
  const ref = useRef(null);

  useFrame((_, delta) => {
    if (!ref.current) return;
    ref.current.rotation.y += delta * 0.008;
    ref.current.position.y -= delta * 0.1;
    if (ref.current.position.y < -0.9) ref.current.position.y = 0.4;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[points, 3]} />
      </bufferGeometry>
      <pointsMaterial size={0.032} color="#f2fbff" transparent opacity={0.68} />
    </points>
  );
}

useGLTF.preload(MODEL_URLS.environment);
useGLTF.preload(MODEL_URLS.meadow);
useGLTF.preload(MODEL_URLS.climber);
useGLTF.preload(MODEL_URLS.sheep);
useGLTF.preload(MODEL_URLS.cableCar);
useGLTF.preload(MODEL_URLS.camp);

export default App;

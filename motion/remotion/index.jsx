import React from "react";
import {AbsoluteFill, Composition, interpolate, registerRoot, useCurrentFrame} from "remotion";

function Title({brand, model, accent}) {
  const frame = useCurrentFrame();
  const offset = interpolate(frame, [0, 16], [110, 0], {extrapolateRight: "clamp"});
  const opacity = interpolate(frame, [0, 12, 76, 89], [0, 1, 1, 0], {extrapolateRight: "clamp"});
  return <AbsoluteFill style={{justifyContent:"center", background:"#101928", color:"white", fontFamily:"sans-serif", padding:100}}>
    <div style={{transform:`translateX(${offset}px)`, opacity}}>
      <div style={{fontSize:44, fontWeight:700, letterSpacing:8}}>{model}</div>
      <div style={{fontSize:158, fontWeight:900, fontStyle:"italic", color:accent}}>{brand}</div>
      <div style={{background:accent, height:9, width:200}} />
    </div>
  </AbsoluteFill>;
}

function Root() {
  return <>
  <Composition id="NelvisTitre" component={Title} fps={30} width={1080} height={1920}
    durationInFrames={90} defaultProps={{brand:"VOLT", model:"RIFT 01", accent:"#dcfa4c"}} />
  <Composition id="NelvisTitreHorizontal" component={Title} fps={30} width={1920} height={1080}
    durationInFrames={90} defaultProps={{brand:"VOLT", model:"RIFT 01", accent:"#dcfa4c"}} />
  </>;
}

registerRoot(Root);

// A missing report is not a rules-based plan. Null also covers imports and failed planning.
export function plannerPresentation(status,offline=false,cloud=false){
 if(offline)return {label:'unknown',disclosure:cloud?'cloudDepends':'plannerDepends'};
 const planner=status?.planner;
 return {
  label:planner===undefined?'plannerNotReported':planner===null?'plannerUnset':`planner_${planner}`,
  disclosure:cloud?(planner==='bedrock'?'cloudBedrock':planner==='nebius'?'cloudNebius':['rules','ollama'].includes(planner)?'cloudLocal':'cloudDepends'):(planner==='bedrock'?'bedrockPrivacy':planner==='nebius'?'crossBorder':['rules','ollama'].includes(planner)?'plannerLocal':'plannerDepends')
 };
}

export function liveKind(recipe){
 if(recipe?.blocks.some(b=>b.type==='color_finder'))return 'target';
 if(recipe?.blocks.some(b=>b.type==='line_counter'))return 'counter';
 return recipe?'privacy_guard':'unknown';
}

// Selection belongs to the runner session, never to the portable recipe or localStorage.
export function cameraChoice(status,previous={}){
 const session_id=status?.session_id,slots=status?.data.cameras||[];
 const camera_id=previous.session_id===session_id&&slots.includes(previous.camera_id)?previous.camera_id:slots[0]||null;
 return {session_id,slots,camera_id};
}
export function withCamera(input,status,selection){
 const {camera_id}=cameraChoice(status,selection);
 return camera_id?{...input,camera_id}:input;
}

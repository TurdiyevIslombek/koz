// A missing report is not a rules-based plan. Null also covers imports and failed planning.
export function plannerPresentation(status,offline=false){
 if(offline)return {label:'unknown',disclosure:'plannerDepends'};
 const planner=status?.planner;
 return {
  label:planner===undefined?'plannerNotReported':planner===null?'plannerUnset':`planner_${planner}`,
  disclosure:planner==='nebius'?'crossBorder':['rules','ollama'].includes(planner)?'plannerLocal':'plannerDepends'
 };
}

export function liveKind(recipe){
 if(recipe?.blocks.some(b=>b.type==='color_finder'))return 'target';
 if(recipe?.blocks.some(b=>b.type==='line_counter'))return 'counter';
 return recipe?'privacy_guard':'unknown';
}

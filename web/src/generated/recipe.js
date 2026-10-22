// Generated from contracts/recipe.schema.json. Do not hand-edit.
import ajvEqual from 'ajv/dist/runtime/equal.js';
"use strict";
export const validate = validate20;
export default validate20;
const schema31 = {"$schema":"https://json-schema.org/draft/2020-12/schema","title":"Ko'z recipe, version 1","$comment":"Structural check only. contracts/events.md section 3 lists the extra checks the runner must also make. A recipe never holds device setup (camera address, ownership, allowed area, motor arming).","type":"object","additionalProperties":false,"required":["version","language","camera","blocks","brain","actions","privacy"],"properties":{"version":{"const":1},"language":{"enum":["uz","ru","en"]},"camera":{"type":"object","additionalProperties":false,"required":["source","size","fps"],"properties":{"source":{"const":"device_camera"},"size":{"enum":["320x240","640x480"]},"fps":{"type":"integer","minimum":1,"maximum":15}}},"blocks":{"type":"array","minItems":2,"maxItems":7,"prefixItems":[{"$ref":"#/$defs/privacy_guard"},{"$ref":"#/$defs/face_blur"}],"items":{"oneOf":[{"$ref":"#/$defs/color_finder"},{"$ref":"#/$defs/object_finder"},{"$ref":"#/$defs/motion_zone"},{"$ref":"#/$defs/person_detector"},{"$ref":"#/$defs/line_counter"},{"$ref":"#/$defs/looming"}]}},"brain":{"oneOf":[{"$ref":"#/$defs/brain_none"},{"$ref":"#/$defs/brain_flybrain"}]},"actions":{"type":"array","minItems":1,"maxItems":2,"prefixItems":[{"type":"object","additionalProperties":false,"required":["type"],"properties":{"type":{"const":"dashboard"}}}],"items":{"oneOf":[{"$ref":"#/$defs/alert"},{"$ref":"#/$defs/motors"}]}},"privacy":{"type":"object","additionalProperties":false,"required":["school"],"properties":{"school":{"type":"boolean"}}}},"allOf":[{"$comment":"Rule 6: school mode allows counting only.","if":{"required":["privacy"],"properties":{"privacy":{"required":["school"],"properties":{"school":{"const":true}}}}},"then":{"properties":{"brain":{"$ref":"#/$defs/brain_none"},"blocks":{"items":{"oneOf":[{"$ref":"#/$defs/privacy_guard"},{"$ref":"#/$defs/face_blur"},{"$ref":"#/$defs/person_detector"},{"$ref":"#/$defs/line_counter"}]}},"actions":{"const":[{"type":"dashboard"}]}}}},{"$comment":"Rule 11: motors only with the fly brain, and the fly brain only reads color_finder.","if":{"required":["brain"],"properties":{"brain":{"required":["type"],"properties":{"type":{"const":"flybrain"}}}}},"then":{"properties":{"blocks":{"contains":{"$ref":"#/$defs/is_color_finder"}},"actions":{"contains":{"$ref":"#/$defs/is_motors"}}}},"else":{"properties":{"actions":{"not":{"contains":{"$ref":"#/$defs/is_motors"}}}}}},{"$comment":"One finder per recipe (Codex review, Oct 22): a thing must never stand in for the car's ball in a check.","not":{"required":["blocks"],"properties":{"blocks":{"allOf":[{"contains":{"$ref":"#/$defs/is_color_finder"}},{"contains":{"$ref":"#/$defs/is_object_finder"}}]}}}},{"$comment":"line_counter counts person_detector results.","if":{"required":["blocks"],"properties":{"blocks":{"contains":{"$ref":"#/$defs/is_line_counter"}}}},"then":{"properties":{"blocks":{"contains":{"$ref":"#/$defs/is_person_detector"}}}}}],"$defs":{"point":{"type":"array","minItems":2,"maxItems":2,"items":{"type":"number","minimum":0,"maximum":1}},"rect":{"$comment":"[left, top, right, bottom], normalized 0..1; left < right and top < bottom are checked by the runner.","type":"array","minItems":4,"maxItems":4,"items":{"type":"number","minimum":0,"maximum":1}},"no_settings":{"type":"object","additionalProperties":false,"maxProperties":0},"privacy_guard":{"$comment":"Locked: fixed code policy, nothing to tune.","type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"privacy_guard"},"settings":{"$ref":"#/$defs/no_settings"}}},"face_blur":{"$comment":"Locked: fixed code policy, nothing to tune.","type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"face_blur"},"settings":{"$ref":"#/$defs/no_settings"}}},"color_finder":{"type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"color_finder"},"settings":{"type":"object","additionalProperties":false,"required":["hue_center","hue_half_width","saturation_min","value_min","min_area_ratio"],"properties":{"hue_center":{"type":"integer","minimum":0,"maximum":179},"hue_half_width":{"type":"integer","minimum":1,"maximum":30},"saturation_min":{"type":"integer","minimum":50,"maximum":255},"value_min":{"type":"integer","minimum":30,"maximum":255},"min_area_ratio":{"type":"number","minimum":0.001,"maximum":0.25}}}}},"object_finder":{"$comment":"Oct 22: one kind of everyday thing (COCO, NanoDet on OpenCV 5), optionally of one colour; reported like color_finder. Never people or animals (rules 4, 11); never the car's input.","type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"object_finder"},"settings":{"type":"object","additionalProperties":false,"required":["object","colour","min_confidence"],"properties":{"object":{"enum":["cell phone","backpack","handbag","suitcase","umbrella","bottle","cup","bowl","laptop","keyboard","mouse","remote","book","clock","chair","scissors","teddy bear","apple","banana","tv","vase","potted plant","bicycle"]},"colour":{"enum":["any","red","orange","yellow","green","blue","purple","white","black","grey"]},"min_confidence":{"type":"number","minimum":0.3,"maximum":0.95}}}}},"motion_zone":{"type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"motion_zone"},"settings":{"type":"object","additionalProperties":false,"required":["rect","pixel_delta","min_changed_ratio"],"properties":{"rect":{"$ref":"#/$defs/rect"},"pixel_delta":{"type":"integer","minimum":10,"maximum":80},"min_changed_ratio":{"type":"number","minimum":0.01,"maximum":0.5}}}}},"person_detector":{"type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"person_detector"},"settings":{"type":"object","additionalProperties":false,"required":["min_confidence"],"properties":{"min_confidence":{"type":"number","minimum":0.3,"maximum":0.95}}}}},"line_counter":{"type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"line_counter"},"settings":{"type":"object","additionalProperties":false,"required":["line"],"properties":{"line":{"type":"array","minItems":2,"maxItems":2,"items":{"$ref":"#/$defs/point"}}}}}},"looming":{"$comment":"Stretch block. The runner rejects it unless status.capabilities lists looming.","type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"looming"},"settings":{"type":"object","additionalProperties":false,"required":["min_expansion_per_second"],"properties":{"min_expansion_per_second":{"type":"number","minimum":0.1,"maximum":5}}}}},"brain_none":{"type":"object","additionalProperties":false,"required":["type"],"properties":{"type":{"const":"none"}}},"brain_flybrain":{"$comment":"Steering reads only color_finder (and looming when present), never person results.","type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"flybrain"},"settings":{"type":"object","additionalProperties":false,"required":["turn_gain","deadband"],"properties":{"turn_gain":{"type":"number","minimum":0.1,"maximum":2},"deadband":{"type":"number","minimum":0.02,"maximum":0.25}}}}},"alert":{"$comment":"In-app badge with a fixed message. No email, SMS, police or discipline reports.","type":"object","additionalProperties":false,"required":["type","template"],"properties":{"type":{"const":"alert"},"template":{"enum":["motion_detected","count_changed"]}}},"motors":{"$comment":"The runner uses the lower of this and the local tested speed cap. Cannot arm motors.","type":"object","additionalProperties":false,"required":["type","max_speed_ratio"],"properties":{"type":{"const":"motors"},"max_speed_ratio":{"type":"number","minimum":0.05,"maximum":0.25}}},"is_color_finder":{"type":"object","required":["type"],"properties":{"type":{"const":"color_finder"}}},"is_object_finder":{"type":"object","required":["type"],"properties":{"type":{"const":"object_finder"}}},"is_person_detector":{"type":"object","required":["type"],"properties":{"type":{"const":"person_detector"}}},"is_line_counter":{"type":"object","required":["type"],"properties":{"type":{"const":"line_counter"}}},"is_motors":{"type":"object","required":["type"],"properties":{"type":{"const":"motors"}}}}};
const schema32 = {"type":"object","additionalProperties":false,"required":["type"],"properties":{"type":{"const":"none"}}};
const schema37 = {"type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"person_detector"},"settings":{"type":"object","additionalProperties":false,"required":["min_confidence"],"properties":{"min_confidence":{"type":"number","minimum":0.3,"maximum":0.95}}}}};
const schema40 = {"type":"object","required":["type"],"properties":{"type":{"const":"color_finder"}}};
const schema41 = {"type":"object","required":["type"],"properties":{"type":{"const":"motors"}}};
const schema44 = {"type":"object","required":["type"],"properties":{"type":{"const":"object_finder"}}};
const schema45 = {"type":"object","required":["type"],"properties":{"type":{"const":"line_counter"}}};
const schema46 = {"type":"object","required":["type"],"properties":{"type":{"const":"person_detector"}}};
const schema47 = {"type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"color_finder"},"settings":{"type":"object","additionalProperties":false,"required":["hue_center","hue_half_width","saturation_min","value_min","min_area_ratio"],"properties":{"hue_center":{"type":"integer","minimum":0,"maximum":179},"hue_half_width":{"type":"integer","minimum":1,"maximum":30},"saturation_min":{"type":"integer","minimum":50,"maximum":255},"value_min":{"type":"integer","minimum":30,"maximum":255},"min_area_ratio":{"type":"number","minimum":0.001,"maximum":0.25}}}}};
const schema48 = {"$comment":"Oct 22: one kind of everyday thing (COCO, NanoDet on OpenCV 5), optionally of one colour; reported like color_finder. Never people or animals (rules 4, 11); never the car's input.","type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"object_finder"},"settings":{"type":"object","additionalProperties":false,"required":["object","colour","min_confidence"],"properties":{"object":{"enum":["cell phone","backpack","handbag","suitcase","umbrella","bottle","cup","bowl","laptop","keyboard","mouse","remote","book","clock","chair","scissors","teddy bear","apple","banana","tv","vase","potted plant","bicycle"]},"colour":{"enum":["any","red","orange","yellow","green","blue","purple","white","black","grey"]},"min_confidence":{"type":"number","minimum":0.3,"maximum":0.95}}}}};
const schema52 = {"$comment":"Stretch block. The runner rejects it unless status.capabilities lists looming.","type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"looming"},"settings":{"type":"object","additionalProperties":false,"required":["min_expansion_per_second"],"properties":{"min_expansion_per_second":{"type":"number","minimum":0.1,"maximum":5}}}}};
const schema54 = {"$comment":"Steering reads only color_finder (and looming when present), never person results.","type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"flybrain"},"settings":{"type":"object","additionalProperties":false,"required":["turn_gain","deadband"],"properties":{"turn_gain":{"type":"number","minimum":0.1,"maximum":2},"deadband":{"type":"number","minimum":0.02,"maximum":0.25}}}}};
const schema55 = {"$comment":"In-app badge with a fixed message. No email, SMS, police or discipline reports.","type":"object","additionalProperties":false,"required":["type","template"],"properties":{"type":{"const":"alert"},"template":{"enum":["motion_detected","count_changed"]}}};
const schema56 = {"$comment":"The runner uses the lower of this and the local tested speed cap. Cannot arm motors.","type":"object","additionalProperties":false,"required":["type","max_speed_ratio"],"properties":{"type":{"const":"motors"},"max_speed_ratio":{"type":"number","minimum":0.05,"maximum":0.25}}};
const schema33 = {"$comment":"Locked: fixed code policy, nothing to tune.","type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"privacy_guard"},"settings":{"$ref":"#/$defs/no_settings"}}};
const schema34 = {"type":"object","additionalProperties":false,"maxProperties":0};

function validate21(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate21.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.type === undefined){
const err0 = {instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
if(data.settings === undefined){
const err1 = {instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: "settings"},message:"must have required property '"+"settings"+"'"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
for(const key0 in data){
if(!((key0 === "type") || (key0 === "settings"))){
const err2 = {instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
}
if(data.type !== undefined){
if("privacy_guard" !== data.type){
const err3 = {instancePath:instancePath+"/type",schemaPath:"#/properties/type/const",keyword:"const",params:{allowedValue: "privacy_guard"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
}
if(data.settings !== undefined){
let data1 = data.settings;
if(data1 && typeof data1 == "object" && !Array.isArray(data1)){
if(Object.keys(data1).length > 0){
const err4 = {instancePath:instancePath+"/settings",schemaPath:"#/$defs/no_settings/maxProperties",keyword:"maxProperties",params:{limit: 0},message:"must NOT have more than 0 properties"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
for(const key1 in data1){
const err5 = {instancePath:instancePath+"/settings",schemaPath:"#/$defs/no_settings/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
}
else {
const err6 = {instancePath:instancePath+"/settings",schemaPath:"#/$defs/no_settings/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
}
}
}
else {
const err7 = {instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
validate21.errors = vErrors;
return errors === 0;
}
validate21.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

const schema35 = {"$comment":"Locked: fixed code policy, nothing to tune.","type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"face_blur"},"settings":{"$ref":"#/$defs/no_settings"}}};

function validate23(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate23.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.type === undefined){
const err0 = {instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
if(data.settings === undefined){
const err1 = {instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: "settings"},message:"must have required property '"+"settings"+"'"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
for(const key0 in data){
if(!((key0 === "type") || (key0 === "settings"))){
const err2 = {instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
}
if(data.type !== undefined){
if("face_blur" !== data.type){
const err3 = {instancePath:instancePath+"/type",schemaPath:"#/properties/type/const",keyword:"const",params:{allowedValue: "face_blur"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
}
if(data.settings !== undefined){
let data1 = data.settings;
if(data1 && typeof data1 == "object" && !Array.isArray(data1)){
if(Object.keys(data1).length > 0){
const err4 = {instancePath:instancePath+"/settings",schemaPath:"#/$defs/no_settings/maxProperties",keyword:"maxProperties",params:{limit: 0},message:"must NOT have more than 0 properties"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
for(const key1 in data1){
const err5 = {instancePath:instancePath+"/settings",schemaPath:"#/$defs/no_settings/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
}
else {
const err6 = {instancePath:instancePath+"/settings",schemaPath:"#/$defs/no_settings/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
}
}
}
else {
const err7 = {instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
validate23.errors = vErrors;
return errors === 0;
}
validate23.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

const schema38 = {"type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"line_counter"},"settings":{"type":"object","additionalProperties":false,"required":["line"],"properties":{"line":{"type":"array","minItems":2,"maxItems":2,"items":{"$ref":"#/$defs/point"}}}}}};
const schema39 = {"type":"array","minItems":2,"maxItems":2,"items":{"type":"number","minimum":0,"maximum":1}};

function validate25(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate25.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.type === undefined){
const err0 = {instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
if(data.settings === undefined){
const err1 = {instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: "settings"},message:"must have required property '"+"settings"+"'"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
for(const key0 in data){
if(!((key0 === "type") || (key0 === "settings"))){
const err2 = {instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
}
if(data.type !== undefined){
if("line_counter" !== data.type){
const err3 = {instancePath:instancePath+"/type",schemaPath:"#/properties/type/const",keyword:"const",params:{allowedValue: "line_counter"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
}
if(data.settings !== undefined){
let data1 = data.settings;
if(data1 && typeof data1 == "object" && !Array.isArray(data1)){
if(data1.line === undefined){
const err4 = {instancePath:instancePath+"/settings",schemaPath:"#/properties/settings/required",keyword:"required",params:{missingProperty: "line"},message:"must have required property '"+"line"+"'"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
for(const key1 in data1){
if(!(key1 === "line")){
const err5 = {instancePath:instancePath+"/settings",schemaPath:"#/properties/settings/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
}
if(data1.line !== undefined){
let data2 = data1.line;
if(Array.isArray(data2)){
if(data2.length > 2){
const err6 = {instancePath:instancePath+"/settings/line",schemaPath:"#/properties/settings/properties/line/maxItems",keyword:"maxItems",params:{limit: 2},message:"must NOT have more than 2 items"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
}
if(data2.length < 2){
const err7 = {instancePath:instancePath+"/settings/line",schemaPath:"#/properties/settings/properties/line/minItems",keyword:"minItems",params:{limit: 2},message:"must NOT have fewer than 2 items"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
const len0 = data2.length;
for(let i0=0; i0<len0; i0++){
let data3 = data2[i0];
if(Array.isArray(data3)){
if(data3.length > 2){
const err8 = {instancePath:instancePath+"/settings/line/" + i0,schemaPath:"#/$defs/point/maxItems",keyword:"maxItems",params:{limit: 2},message:"must NOT have more than 2 items"};
if(vErrors === null){
vErrors = [err8];
}
else {
vErrors.push(err8);
}
errors++;
}
if(data3.length < 2){
const err9 = {instancePath:instancePath+"/settings/line/" + i0,schemaPath:"#/$defs/point/minItems",keyword:"minItems",params:{limit: 2},message:"must NOT have fewer than 2 items"};
if(vErrors === null){
vErrors = [err9];
}
else {
vErrors.push(err9);
}
errors++;
}
const len1 = data3.length;
for(let i1=0; i1<len1; i1++){
let data4 = data3[i1];
if(typeof data4 == "number"){
if(data4 > 1 || isNaN(data4)){
const err10 = {instancePath:instancePath+"/settings/line/" + i0+"/" + i1,schemaPath:"#/$defs/point/items/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1},message:"must be <= 1"};
if(vErrors === null){
vErrors = [err10];
}
else {
vErrors.push(err10);
}
errors++;
}
if(data4 < 0 || isNaN(data4)){
const err11 = {instancePath:instancePath+"/settings/line/" + i0+"/" + i1,schemaPath:"#/$defs/point/items/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err11];
}
else {
vErrors.push(err11);
}
errors++;
}
}
else {
const err12 = {instancePath:instancePath+"/settings/line/" + i0+"/" + i1,schemaPath:"#/$defs/point/items/type",keyword:"type",params:{type: "number"},message:"must be number"};
if(vErrors === null){
vErrors = [err12];
}
else {
vErrors.push(err12);
}
errors++;
}
}
}
else {
const err13 = {instancePath:instancePath+"/settings/line/" + i0,schemaPath:"#/$defs/point/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err13];
}
else {
vErrors.push(err13);
}
errors++;
}
}
}
else {
const err14 = {instancePath:instancePath+"/settings/line",schemaPath:"#/properties/settings/properties/line/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err14];
}
else {
vErrors.push(err14);
}
errors++;
}
}
}
else {
const err15 = {instancePath:instancePath+"/settings",schemaPath:"#/properties/settings/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err15];
}
else {
vErrors.push(err15);
}
errors++;
}
}
}
else {
const err16 = {instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err16];
}
else {
vErrors.push(err16);
}
errors++;
}
validate25.errors = vErrors;
return errors === 0;
}
validate25.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

const schema49 = {"type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"motion_zone"},"settings":{"type":"object","additionalProperties":false,"required":["rect","pixel_delta","min_changed_ratio"],"properties":{"rect":{"$ref":"#/$defs/rect"},"pixel_delta":{"type":"integer","minimum":10,"maximum":80},"min_changed_ratio":{"type":"number","minimum":0.01,"maximum":0.5}}}}};
const schema50 = {"$comment":"[left, top, right, bottom], normalized 0..1; left < right and top < bottom are checked by the runner.","type":"array","minItems":4,"maxItems":4,"items":{"type":"number","minimum":0,"maximum":1}};

function validate29(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate29.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.type === undefined){
const err0 = {instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
if(data.settings === undefined){
const err1 = {instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: "settings"},message:"must have required property '"+"settings"+"'"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
for(const key0 in data){
if(!((key0 === "type") || (key0 === "settings"))){
const err2 = {instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
}
if(data.type !== undefined){
if("motion_zone" !== data.type){
const err3 = {instancePath:instancePath+"/type",schemaPath:"#/properties/type/const",keyword:"const",params:{allowedValue: "motion_zone"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
}
if(data.settings !== undefined){
let data1 = data.settings;
if(data1 && typeof data1 == "object" && !Array.isArray(data1)){
if(data1.rect === undefined){
const err4 = {instancePath:instancePath+"/settings",schemaPath:"#/properties/settings/required",keyword:"required",params:{missingProperty: "rect"},message:"must have required property '"+"rect"+"'"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
if(data1.pixel_delta === undefined){
const err5 = {instancePath:instancePath+"/settings",schemaPath:"#/properties/settings/required",keyword:"required",params:{missingProperty: "pixel_delta"},message:"must have required property '"+"pixel_delta"+"'"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
if(data1.min_changed_ratio === undefined){
const err6 = {instancePath:instancePath+"/settings",schemaPath:"#/properties/settings/required",keyword:"required",params:{missingProperty: "min_changed_ratio"},message:"must have required property '"+"min_changed_ratio"+"'"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
}
for(const key1 in data1){
if(!(((key1 === "rect") || (key1 === "pixel_delta")) || (key1 === "min_changed_ratio"))){
const err7 = {instancePath:instancePath+"/settings",schemaPath:"#/properties/settings/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
}
if(data1.rect !== undefined){
let data2 = data1.rect;
if(Array.isArray(data2)){
if(data2.length > 4){
const err8 = {instancePath:instancePath+"/settings/rect",schemaPath:"#/$defs/rect/maxItems",keyword:"maxItems",params:{limit: 4},message:"must NOT have more than 4 items"};
if(vErrors === null){
vErrors = [err8];
}
else {
vErrors.push(err8);
}
errors++;
}
if(data2.length < 4){
const err9 = {instancePath:instancePath+"/settings/rect",schemaPath:"#/$defs/rect/minItems",keyword:"minItems",params:{limit: 4},message:"must NOT have fewer than 4 items"};
if(vErrors === null){
vErrors = [err9];
}
else {
vErrors.push(err9);
}
errors++;
}
const len0 = data2.length;
for(let i0=0; i0<len0; i0++){
let data3 = data2[i0];
if(typeof data3 == "number"){
if(data3 > 1 || isNaN(data3)){
const err10 = {instancePath:instancePath+"/settings/rect/" + i0,schemaPath:"#/$defs/rect/items/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1},message:"must be <= 1"};
if(vErrors === null){
vErrors = [err10];
}
else {
vErrors.push(err10);
}
errors++;
}
if(data3 < 0 || isNaN(data3)){
const err11 = {instancePath:instancePath+"/settings/rect/" + i0,schemaPath:"#/$defs/rect/items/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err11];
}
else {
vErrors.push(err11);
}
errors++;
}
}
else {
const err12 = {instancePath:instancePath+"/settings/rect/" + i0,schemaPath:"#/$defs/rect/items/type",keyword:"type",params:{type: "number"},message:"must be number"};
if(vErrors === null){
vErrors = [err12];
}
else {
vErrors.push(err12);
}
errors++;
}
}
}
else {
const err13 = {instancePath:instancePath+"/settings/rect",schemaPath:"#/$defs/rect/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err13];
}
else {
vErrors.push(err13);
}
errors++;
}
}
if(data1.pixel_delta !== undefined){
let data4 = data1.pixel_delta;
if(!((typeof data4 == "number") && (!(data4 % 1) && !isNaN(data4)))){
const err14 = {instancePath:instancePath+"/settings/pixel_delta",schemaPath:"#/properties/settings/properties/pixel_delta/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err14];
}
else {
vErrors.push(err14);
}
errors++;
}
if(typeof data4 == "number"){
if(data4 > 80 || isNaN(data4)){
const err15 = {instancePath:instancePath+"/settings/pixel_delta",schemaPath:"#/properties/settings/properties/pixel_delta/maximum",keyword:"maximum",params:{comparison: "<=", limit: 80},message:"must be <= 80"};
if(vErrors === null){
vErrors = [err15];
}
else {
vErrors.push(err15);
}
errors++;
}
if(data4 < 10 || isNaN(data4)){
const err16 = {instancePath:instancePath+"/settings/pixel_delta",schemaPath:"#/properties/settings/properties/pixel_delta/minimum",keyword:"minimum",params:{comparison: ">=", limit: 10},message:"must be >= 10"};
if(vErrors === null){
vErrors = [err16];
}
else {
vErrors.push(err16);
}
errors++;
}
}
}
if(data1.min_changed_ratio !== undefined){
let data5 = data1.min_changed_ratio;
if(typeof data5 == "number"){
if(data5 > 0.5 || isNaN(data5)){
const err17 = {instancePath:instancePath+"/settings/min_changed_ratio",schemaPath:"#/properties/settings/properties/min_changed_ratio/maximum",keyword:"maximum",params:{comparison: "<=", limit: 0.5},message:"must be <= 0.5"};
if(vErrors === null){
vErrors = [err17];
}
else {
vErrors.push(err17);
}
errors++;
}
if(data5 < 0.01 || isNaN(data5)){
const err18 = {instancePath:instancePath+"/settings/min_changed_ratio",schemaPath:"#/properties/settings/properties/min_changed_ratio/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0.01},message:"must be >= 0.01"};
if(vErrors === null){
vErrors = [err18];
}
else {
vErrors.push(err18);
}
errors++;
}
}
else {
const err19 = {instancePath:instancePath+"/settings/min_changed_ratio",schemaPath:"#/properties/settings/properties/min_changed_ratio/type",keyword:"type",params:{type: "number"},message:"must be number"};
if(vErrors === null){
vErrors = [err19];
}
else {
vErrors.push(err19);
}
errors++;
}
}
}
else {
const err20 = {instancePath:instancePath+"/settings",schemaPath:"#/properties/settings/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err20];
}
else {
vErrors.push(err20);
}
errors++;
}
}
}
else {
const err21 = {instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err21];
}
else {
vErrors.push(err21);
}
errors++;
}
validate29.errors = vErrors;
return errors === 0;
}
validate29.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

const func0 = ajvEqual.default;

function validate20(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate20.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
const _errs4 = errors;
let valid1 = true;
const _errs5 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((data.privacy === undefined) && (missing0 = "privacy")){
const err0 = {};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
else {
if(data.privacy !== undefined){
let data0 = data.privacy;
if(data0 && typeof data0 == "object" && !Array.isArray(data0)){
let missing1;
if((data0.school === undefined) && (missing1 = "school")){
const err1 = {};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
else {
if(data0.school !== undefined){
if(true !== data0.school){
const err2 = {};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
}
}
}
}
}
}
var _valid0 = _errs5 === errors;
errors = _errs4;
if(vErrors !== null){
if(_errs4){
vErrors.length = _errs4;
}
else {
vErrors = null;
}
}
if(_valid0){
const _errs8 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.brain !== undefined){
let data2 = data.brain;
if(data2 && typeof data2 == "object" && !Array.isArray(data2)){
if(data2.type === undefined){
const err3 = {instancePath:instancePath+"/brain",schemaPath:"#/$defs/brain_none/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
for(const key0 in data2){
if(!(key0 === "type")){
const err4 = {instancePath:instancePath+"/brain",schemaPath:"#/$defs/brain_none/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
}
if(data2.type !== undefined){
if("none" !== data2.type){
const err5 = {instancePath:instancePath+"/brain/type",schemaPath:"#/$defs/brain_none/properties/type/const",keyword:"const",params:{allowedValue: "none"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
}
}
else {
const err6 = {instancePath:instancePath+"/brain",schemaPath:"#/$defs/brain_none/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
}
}
if(data.blocks !== undefined){
let data4 = data.blocks;
if(Array.isArray(data4)){
const len0 = data4.length;
for(let i0=0; i0<len0; i0++){
let data5 = data4[i0];
const _errs16 = errors;
let valid9 = false;
let passing0 = null;
const _errs17 = errors;
if(!(validate21(data5, {instancePath:instancePath+"/blocks/" + i0,parentData:data4,parentDataProperty:i0,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate21.errors : vErrors.concat(validate21.errors);
errors = vErrors.length;
}
var _valid1 = _errs17 === errors;
if(_valid1){
valid9 = true;
passing0 = 0;
var props0 = true;
}
const _errs18 = errors;
if(!(validate23(data5, {instancePath:instancePath+"/blocks/" + i0,parentData:data4,parentDataProperty:i0,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate23.errors : vErrors.concat(validate23.errors);
errors = vErrors.length;
}
var _valid1 = _errs18 === errors;
if(_valid1 && valid9){
valid9 = false;
passing0 = [passing0, 1];
}
else {
if(_valid1){
valid9 = true;
passing0 = 1;
if(props0 !== true){
props0 = true;
}
}
const _errs19 = errors;
if(data5 && typeof data5 == "object" && !Array.isArray(data5)){
if(data5.type === undefined){
const err7 = {instancePath:instancePath+"/blocks/" + i0,schemaPath:"#/$defs/person_detector/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
if(data5.settings === undefined){
const err8 = {instancePath:instancePath+"/blocks/" + i0,schemaPath:"#/$defs/person_detector/required",keyword:"required",params:{missingProperty: "settings"},message:"must have required property '"+"settings"+"'"};
if(vErrors === null){
vErrors = [err8];
}
else {
vErrors.push(err8);
}
errors++;
}
for(const key1 in data5){
if(!((key1 === "type") || (key1 === "settings"))){
const err9 = {instancePath:instancePath+"/blocks/" + i0,schemaPath:"#/$defs/person_detector/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err9];
}
else {
vErrors.push(err9);
}
errors++;
}
}
if(data5.type !== undefined){
if("person_detector" !== data5.type){
const err10 = {instancePath:instancePath+"/blocks/" + i0+"/type",schemaPath:"#/$defs/person_detector/properties/type/const",keyword:"const",params:{allowedValue: "person_detector"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err10];
}
else {
vErrors.push(err10);
}
errors++;
}
}
if(data5.settings !== undefined){
let data7 = data5.settings;
if(data7 && typeof data7 == "object" && !Array.isArray(data7)){
if(data7.min_confidence === undefined){
const err11 = {instancePath:instancePath+"/blocks/" + i0+"/settings",schemaPath:"#/$defs/person_detector/properties/settings/required",keyword:"required",params:{missingProperty: "min_confidence"},message:"must have required property '"+"min_confidence"+"'"};
if(vErrors === null){
vErrors = [err11];
}
else {
vErrors.push(err11);
}
errors++;
}
for(const key2 in data7){
if(!(key2 === "min_confidence")){
const err12 = {instancePath:instancePath+"/blocks/" + i0+"/settings",schemaPath:"#/$defs/person_detector/properties/settings/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key2},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err12];
}
else {
vErrors.push(err12);
}
errors++;
}
}
if(data7.min_confidence !== undefined){
let data8 = data7.min_confidence;
if(typeof data8 == "number"){
if(data8 > 0.95 || isNaN(data8)){
const err13 = {instancePath:instancePath+"/blocks/" + i0+"/settings/min_confidence",schemaPath:"#/$defs/person_detector/properties/settings/properties/min_confidence/maximum",keyword:"maximum",params:{comparison: "<=", limit: 0.95},message:"must be <= 0.95"};
if(vErrors === null){
vErrors = [err13];
}
else {
vErrors.push(err13);
}
errors++;
}
if(data8 < 0.3 || isNaN(data8)){
const err14 = {instancePath:instancePath+"/blocks/" + i0+"/settings/min_confidence",schemaPath:"#/$defs/person_detector/properties/settings/properties/min_confidence/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0.3},message:"must be >= 0.3"};
if(vErrors === null){
vErrors = [err14];
}
else {
vErrors.push(err14);
}
errors++;
}
}
else {
const err15 = {instancePath:instancePath+"/blocks/" + i0+"/settings/min_confidence",schemaPath:"#/$defs/person_detector/properties/settings/properties/min_confidence/type",keyword:"type",params:{type: "number"},message:"must be number"};
if(vErrors === null){
vErrors = [err15];
}
else {
vErrors.push(err15);
}
errors++;
}
}
}
else {
const err16 = {instancePath:instancePath+"/blocks/" + i0+"/settings",schemaPath:"#/$defs/person_detector/properties/settings/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err16];
}
else {
vErrors.push(err16);
}
errors++;
}
}
}
else {
const err17 = {instancePath:instancePath+"/blocks/" + i0,schemaPath:"#/$defs/person_detector/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err17];
}
else {
vErrors.push(err17);
}
errors++;
}
var _valid1 = _errs19 === errors;
if(_valid1 && valid9){
valid9 = false;
passing0 = [passing0, 2];
}
else {
if(_valid1){
valid9 = true;
passing0 = 2;
if(props0 !== true){
props0 = true;
}
}
const _errs29 = errors;
if(!(validate25(data5, {instancePath:instancePath+"/blocks/" + i0,parentData:data4,parentDataProperty:i0,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate25.errors : vErrors.concat(validate25.errors);
errors = vErrors.length;
}
var _valid1 = _errs29 === errors;
if(_valid1 && valid9){
valid9 = false;
passing0 = [passing0, 3];
}
else {
if(_valid1){
valid9 = true;
passing0 = 3;
if(props0 !== true){
props0 = true;
}
}
}
}
}
if(!valid9){
const err18 = {instancePath:instancePath+"/blocks/" + i0,schemaPath:"#/allOf/0/then/properties/blocks/items/oneOf",keyword:"oneOf",params:{passingSchemas: passing0},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err18];
}
else {
vErrors.push(err18);
}
errors++;
}
else {
errors = _errs16;
if(vErrors !== null){
if(_errs16){
vErrors.length = _errs16;
}
else {
vErrors = null;
}
}
}
}
}
}
if(data.actions !== undefined){
if(!func0(data.actions, schema31.allOf[0].then.properties.actions.const)){
const err19 = {instancePath:instancePath+"/actions",schemaPath:"#/allOf/0/then/properties/actions/const",keyword:"const",params:{allowedValue: schema31.allOf[0].then.properties.actions.const},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err19];
}
else {
vErrors.push(err19);
}
errors++;
}
}
}
var _valid0 = _errs8 === errors;
valid1 = _valid0;
if(valid1){
var props1 = {};
props1.brain = true;
props1.blocks = true;
props1.actions = true;
props1.privacy = true;
}
}
if(!valid1){
const err20 = {instancePath,schemaPath:"#/allOf/0/if",keyword:"if",params:{failingKeyword: "then"},message:"must match \"then\" schema"};
if(vErrors === null){
vErrors = [err20];
}
else {
vErrors.push(err20);
}
errors++;
}
const _errs33 = errors;
let valid13 = true;
const _errs34 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
let missing2;
if((data.brain === undefined) && (missing2 = "brain")){
const err21 = {};
if(vErrors === null){
vErrors = [err21];
}
else {
vErrors.push(err21);
}
errors++;
}
else {
if(data.brain !== undefined){
let data10 = data.brain;
if(data10 && typeof data10 == "object" && !Array.isArray(data10)){
let missing3;
if((data10.type === undefined) && (missing3 = "type")){
const err22 = {};
if(vErrors === null){
vErrors = [err22];
}
else {
vErrors.push(err22);
}
errors++;
}
else {
if(data10.type !== undefined){
if("flybrain" !== data10.type){
const err23 = {};
if(vErrors === null){
vErrors = [err23];
}
else {
vErrors.push(err23);
}
errors++;
}
}
}
}
}
}
}
var _valid2 = _errs34 === errors;
errors = _errs33;
if(vErrors !== null){
if(_errs33){
vErrors.length = _errs33;
}
else {
vErrors = null;
}
}
let ifClause0;
if(_valid2){
const _errs37 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.blocks !== undefined){
let data12 = data.blocks;
if(Array.isArray(data12)){
const _errs39 = errors;
const len1 = data12.length;
for(let i1=0; i1<len1; i1++){
let data13 = data12[i1];
const _errs40 = errors;
if(data13 && typeof data13 == "object" && !Array.isArray(data13)){
if(data13.type === undefined){
const err24 = {instancePath:instancePath+"/blocks/" + i1,schemaPath:"#/$defs/is_color_finder/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err24];
}
else {
vErrors.push(err24);
}
errors++;
}
if(data13.type !== undefined){
if("color_finder" !== data13.type){
const err25 = {instancePath:instancePath+"/blocks/" + i1+"/type",schemaPath:"#/$defs/is_color_finder/properties/type/const",keyword:"const",params:{allowedValue: "color_finder"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err25];
}
else {
vErrors.push(err25);
}
errors++;
}
}
}
else {
const err26 = {instancePath:instancePath+"/blocks/" + i1,schemaPath:"#/$defs/is_color_finder/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err26];
}
else {
vErrors.push(err26);
}
errors++;
}
var valid17 = _errs40 === errors;
if(valid17){
break;
}
}
if(!valid17){
const err27 = {instancePath:instancePath+"/blocks",schemaPath:"#/allOf/1/then/properties/blocks/contains",keyword:"contains",params:{minContains: 1},message:"must contain at least 1 valid item(s)"};
if(vErrors === null){
vErrors = [err27];
}
else {
vErrors.push(err27);
}
errors++;
}
else {
errors = _errs39;
if(vErrors !== null){
if(_errs39){
vErrors.length = _errs39;
}
else {
vErrors = null;
}
}
}
}
}
if(data.actions !== undefined){
let data15 = data.actions;
if(Array.isArray(data15)){
const _errs45 = errors;
const len2 = data15.length;
for(let i2=0; i2<len2; i2++){
let data16 = data15[i2];
const _errs46 = errors;
if(data16 && typeof data16 == "object" && !Array.isArray(data16)){
if(data16.type === undefined){
const err28 = {instancePath:instancePath+"/actions/" + i2,schemaPath:"#/$defs/is_motors/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err28];
}
else {
vErrors.push(err28);
}
errors++;
}
if(data16.type !== undefined){
if("motors" !== data16.type){
const err29 = {instancePath:instancePath+"/actions/" + i2+"/type",schemaPath:"#/$defs/is_motors/properties/type/const",keyword:"const",params:{allowedValue: "motors"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err29];
}
else {
vErrors.push(err29);
}
errors++;
}
}
}
else {
const err30 = {instancePath:instancePath+"/actions/" + i2,schemaPath:"#/$defs/is_motors/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err30];
}
else {
vErrors.push(err30);
}
errors++;
}
var valid20 = _errs46 === errors;
if(valid20){
break;
}
}
if(!valid20){
const err31 = {instancePath:instancePath+"/actions",schemaPath:"#/allOf/1/then/properties/actions/contains",keyword:"contains",params:{minContains: 1},message:"must contain at least 1 valid item(s)"};
if(vErrors === null){
vErrors = [err31];
}
else {
vErrors.push(err31);
}
errors++;
}
else {
errors = _errs45;
if(vErrors !== null){
if(_errs45){
vErrors.length = _errs45;
}
else {
vErrors = null;
}
}
}
}
}
}
var _valid2 = _errs37 === errors;
valid13 = _valid2;
if(valid13){
var props2 = {};
props2.blocks = true;
props2.actions = true;
props2.brain = true;
}
ifClause0 = "then";
}
else {
const _errs50 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.actions !== undefined){
let data18 = data.actions;
const _errs52 = errors;
const _errs53 = errors;
if(Array.isArray(data18)){
const _errs54 = errors;
const len3 = data18.length;
for(let i3=0; i3<len3; i3++){
let data19 = data18[i3];
const _errs55 = errors;
const _errs56 = errors;
if(errors === _errs56){
if(data19 && typeof data19 == "object" && !Array.isArray(data19)){
let missing4;
if((data19.type === undefined) && (missing4 = "type")){
const err32 = {};
if(vErrors === null){
vErrors = [err32];
}
else {
vErrors.push(err32);
}
errors++;
}
else {
if(data19.type !== undefined){
if("motors" !== data19.type){
const err33 = {};
if(vErrors === null){
vErrors = [err33];
}
else {
vErrors.push(err33);
}
errors++;
}
}
}
}
else {
const err34 = {};
if(vErrors === null){
vErrors = [err34];
}
else {
vErrors.push(err34);
}
errors++;
}
}
var valid25 = _errs55 === errors;
if(valid25){
break;
}
}
if(!valid25){
const err35 = {};
if(vErrors === null){
vErrors = [err35];
}
else {
vErrors.push(err35);
}
errors++;
}
else {
errors = _errs54;
if(vErrors !== null){
if(_errs54){
vErrors.length = _errs54;
}
else {
vErrors = null;
}
}
}
}
var valid24 = _errs53 === errors;
if(valid24){
const err36 = {instancePath:instancePath+"/actions",schemaPath:"#/allOf/1/else/properties/actions/not",keyword:"not",params:{},message:"must NOT be valid"};
if(vErrors === null){
vErrors = [err36];
}
else {
vErrors.push(err36);
}
errors++;
}
else {
errors = _errs52;
if(vErrors !== null){
if(_errs52){
vErrors.length = _errs52;
}
else {
vErrors = null;
}
}
}
}
}
var _valid2 = _errs50 === errors;
valid13 = _valid2;
if(valid13){
if(props2 !== true){
props2 = props2 || {};
props2.actions = true;
}
}
ifClause0 = "else";
}
if(!valid13){
const err37 = {instancePath,schemaPath:"#/allOf/1/if",keyword:"if",params:{failingKeyword: ifClause0},message:"must match \""+ifClause0+"\" schema"};
if(vErrors === null){
vErrors = [err37];
}
else {
vErrors.push(err37);
}
errors++;
}
if(props1 !== true && props2 !== undefined){
if(props2 === true){
props1 = true;
}
else {
props1 = props1 || {};
Object.assign(props1, props2);
}
}
const _errs61 = errors;
const _errs62 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
let missing5;
if((data.blocks === undefined) && (missing5 = "blocks")){
const err38 = {};
if(vErrors === null){
vErrors = [err38];
}
else {
vErrors.push(err38);
}
errors++;
}
else {
if(data.blocks !== undefined){
let data21 = data.blocks;
const _errs64 = errors;
if(Array.isArray(data21)){
const _errs65 = errors;
const len4 = data21.length;
for(let i4=0; i4<len4; i4++){
let data22 = data21[i4];
const _errs66 = errors;
const _errs67 = errors;
if(errors === _errs67){
if(data22 && typeof data22 == "object" && !Array.isArray(data22)){
let missing6;
if((data22.type === undefined) && (missing6 = "type")){
const err39 = {};
if(vErrors === null){
vErrors = [err39];
}
else {
vErrors.push(err39);
}
errors++;
}
else {
if(data22.type !== undefined){
if("color_finder" !== data22.type){
const err40 = {};
if(vErrors === null){
vErrors = [err40];
}
else {
vErrors.push(err40);
}
errors++;
}
}
}
}
else {
const err41 = {};
if(vErrors === null){
vErrors = [err41];
}
else {
vErrors.push(err41);
}
errors++;
}
}
var valid31 = _errs66 === errors;
if(valid31){
break;
}
}
if(!valid31){
const err42 = {};
if(vErrors === null){
vErrors = [err42];
}
else {
vErrors.push(err42);
}
errors++;
}
else {
errors = _errs65;
if(vErrors !== null){
if(_errs65){
vErrors.length = _errs65;
}
else {
vErrors = null;
}
}
}
}
var valid30 = _errs64 === errors;
if(valid30){
const _errs70 = errors;
if(Array.isArray(data21)){
const _errs71 = errors;
const len5 = data21.length;
for(let i5=0; i5<len5; i5++){
let data24 = data21[i5];
const _errs72 = errors;
const _errs73 = errors;
if(errors === _errs73){
if(data24 && typeof data24 == "object" && !Array.isArray(data24)){
let missing7;
if((data24.type === undefined) && (missing7 = "type")){
const err43 = {};
if(vErrors === null){
vErrors = [err43];
}
else {
vErrors.push(err43);
}
errors++;
}
else {
if(data24.type !== undefined){
if("object_finder" !== data24.type){
const err44 = {};
if(vErrors === null){
vErrors = [err44];
}
else {
vErrors.push(err44);
}
errors++;
}
}
}
}
else {
const err45 = {};
if(vErrors === null){
vErrors = [err45];
}
else {
vErrors.push(err45);
}
errors++;
}
}
var valid34 = _errs72 === errors;
if(valid34){
break;
}
}
if(!valid34){
const err46 = {};
if(vErrors === null){
vErrors = [err46];
}
else {
vErrors.push(err46);
}
errors++;
}
else {
errors = _errs71;
if(vErrors !== null){
if(_errs71){
vErrors.length = _errs71;
}
else {
vErrors = null;
}
}
}
}
var valid30 = _errs70 === errors;
}
}
}
}
var valid28 = _errs62 === errors;
if(valid28){
const err47 = {instancePath,schemaPath:"#/allOf/2/not",keyword:"not",params:{},message:"must NOT be valid"};
if(vErrors === null){
vErrors = [err47];
}
else {
vErrors.push(err47);
}
errors++;
}
else {
errors = _errs61;
if(vErrors !== null){
if(_errs61){
vErrors.length = _errs61;
}
else {
vErrors = null;
}
}
}
const _errs78 = errors;
let valid37 = true;
const _errs79 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
let missing8;
if((data.blocks === undefined) && (missing8 = "blocks")){
const err48 = {};
if(vErrors === null){
vErrors = [err48];
}
else {
vErrors.push(err48);
}
errors++;
}
else {
if(data.blocks !== undefined){
let data26 = data.blocks;
if(Array.isArray(data26)){
const _errs81 = errors;
const len6 = data26.length;
for(let i6=0; i6<len6; i6++){
let data27 = data26[i6];
const _errs82 = errors;
const _errs83 = errors;
if(errors === _errs83){
if(data27 && typeof data27 == "object" && !Array.isArray(data27)){
let missing9;
if((data27.type === undefined) && (missing9 = "type")){
const err49 = {};
if(vErrors === null){
vErrors = [err49];
}
else {
vErrors.push(err49);
}
errors++;
}
else {
if(data27.type !== undefined){
if("line_counter" !== data27.type){
const err50 = {};
if(vErrors === null){
vErrors = [err50];
}
else {
vErrors.push(err50);
}
errors++;
}
}
}
}
else {
const err51 = {};
if(vErrors === null){
vErrors = [err51];
}
else {
vErrors.push(err51);
}
errors++;
}
}
var valid39 = _errs82 === errors;
if(valid39){
break;
}
}
if(!valid39){
const err52 = {};
if(vErrors === null){
vErrors = [err52];
}
else {
vErrors.push(err52);
}
errors++;
}
else {
errors = _errs81;
if(vErrors !== null){
if(_errs81){
vErrors.length = _errs81;
}
else {
vErrors = null;
}
}
}
}
}
}
}
var _valid3 = _errs79 === errors;
errors = _errs78;
if(vErrors !== null){
if(_errs78){
vErrors.length = _errs78;
}
else {
vErrors = null;
}
}
if(_valid3){
const _errs86 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.blocks !== undefined){
let data29 = data.blocks;
if(Array.isArray(data29)){
const _errs88 = errors;
const len7 = data29.length;
for(let i7=0; i7<len7; i7++){
let data30 = data29[i7];
const _errs89 = errors;
if(data30 && typeof data30 == "object" && !Array.isArray(data30)){
if(data30.type === undefined){
const err53 = {instancePath:instancePath+"/blocks/" + i7,schemaPath:"#/$defs/is_person_detector/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err53];
}
else {
vErrors.push(err53);
}
errors++;
}
if(data30.type !== undefined){
if("person_detector" !== data30.type){
const err54 = {instancePath:instancePath+"/blocks/" + i7+"/type",schemaPath:"#/$defs/is_person_detector/properties/type/const",keyword:"const",params:{allowedValue: "person_detector"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err54];
}
else {
vErrors.push(err54);
}
errors++;
}
}
}
else {
const err55 = {instancePath:instancePath+"/blocks/" + i7,schemaPath:"#/$defs/is_person_detector/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err55];
}
else {
vErrors.push(err55);
}
errors++;
}
var valid43 = _errs89 === errors;
if(valid43){
break;
}
}
if(!valid43){
const err56 = {instancePath:instancePath+"/blocks",schemaPath:"#/allOf/3/then/properties/blocks/contains",keyword:"contains",params:{minContains: 1},message:"must contain at least 1 valid item(s)"};
if(vErrors === null){
vErrors = [err56];
}
else {
vErrors.push(err56);
}
errors++;
}
else {
errors = _errs88;
if(vErrors !== null){
if(_errs88){
vErrors.length = _errs88;
}
else {
vErrors = null;
}
}
}
}
}
}
var _valid3 = _errs86 === errors;
valid37 = _valid3;
if(valid37){
var props3 = {};
props3.blocks = true;
}
}
if(!valid37){
const err57 = {instancePath,schemaPath:"#/allOf/3/if",keyword:"if",params:{failingKeyword: "then"},message:"must match \"then\" schema"};
if(vErrors === null){
vErrors = [err57];
}
else {
vErrors.push(err57);
}
errors++;
}
if(props1 !== true && props3 !== undefined){
if(props3 === true){
props1 = true;
}
else {
props1 = props1 || {};
Object.assign(props1, props3);
}
}
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.version === undefined){
const err58 = {instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: "version"},message:"must have required property '"+"version"+"'"};
if(vErrors === null){
vErrors = [err58];
}
else {
vErrors.push(err58);
}
errors++;
}
if(data.language === undefined){
const err59 = {instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: "language"},message:"must have required property '"+"language"+"'"};
if(vErrors === null){
vErrors = [err59];
}
else {
vErrors.push(err59);
}
errors++;
}
if(data.camera === undefined){
const err60 = {instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: "camera"},message:"must have required property '"+"camera"+"'"};
if(vErrors === null){
vErrors = [err60];
}
else {
vErrors.push(err60);
}
errors++;
}
if(data.blocks === undefined){
const err61 = {instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: "blocks"},message:"must have required property '"+"blocks"+"'"};
if(vErrors === null){
vErrors = [err61];
}
else {
vErrors.push(err61);
}
errors++;
}
if(data.brain === undefined){
const err62 = {instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: "brain"},message:"must have required property '"+"brain"+"'"};
if(vErrors === null){
vErrors = [err62];
}
else {
vErrors.push(err62);
}
errors++;
}
if(data.actions === undefined){
const err63 = {instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: "actions"},message:"must have required property '"+"actions"+"'"};
if(vErrors === null){
vErrors = [err63];
}
else {
vErrors.push(err63);
}
errors++;
}
if(data.privacy === undefined){
const err64 = {instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: "privacy"},message:"must have required property '"+"privacy"+"'"};
if(vErrors === null){
vErrors = [err64];
}
else {
vErrors.push(err64);
}
errors++;
}
for(const key3 in data){
if(!(((((((key3 === "version") || (key3 === "language")) || (key3 === "camera")) || (key3 === "blocks")) || (key3 === "brain")) || (key3 === "actions")) || (key3 === "privacy"))){
const err65 = {instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key3},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err65];
}
else {
vErrors.push(err65);
}
errors++;
}
}
if(data.version !== undefined){
if(1 !== data.version){
const err66 = {instancePath:instancePath+"/version",schemaPath:"#/properties/version/const",keyword:"const",params:{allowedValue: 1},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err66];
}
else {
vErrors.push(err66);
}
errors++;
}
}
if(data.language !== undefined){
let data33 = data.language;
if(!(((data33 === "uz") || (data33 === "ru")) || (data33 === "en"))){
const err67 = {instancePath:instancePath+"/language",schemaPath:"#/properties/language/enum",keyword:"enum",params:{allowedValues: schema31.properties.language.enum},message:"must be equal to one of the allowed values"};
if(vErrors === null){
vErrors = [err67];
}
else {
vErrors.push(err67);
}
errors++;
}
}
if(data.camera !== undefined){
let data34 = data.camera;
if(data34 && typeof data34 == "object" && !Array.isArray(data34)){
if(data34.source === undefined){
const err68 = {instancePath:instancePath+"/camera",schemaPath:"#/properties/camera/required",keyword:"required",params:{missingProperty: "source"},message:"must have required property '"+"source"+"'"};
if(vErrors === null){
vErrors = [err68];
}
else {
vErrors.push(err68);
}
errors++;
}
if(data34.size === undefined){
const err69 = {instancePath:instancePath+"/camera",schemaPath:"#/properties/camera/required",keyword:"required",params:{missingProperty: "size"},message:"must have required property '"+"size"+"'"};
if(vErrors === null){
vErrors = [err69];
}
else {
vErrors.push(err69);
}
errors++;
}
if(data34.fps === undefined){
const err70 = {instancePath:instancePath+"/camera",schemaPath:"#/properties/camera/required",keyword:"required",params:{missingProperty: "fps"},message:"must have required property '"+"fps"+"'"};
if(vErrors === null){
vErrors = [err70];
}
else {
vErrors.push(err70);
}
errors++;
}
for(const key4 in data34){
if(!(((key4 === "source") || (key4 === "size")) || (key4 === "fps"))){
const err71 = {instancePath:instancePath+"/camera",schemaPath:"#/properties/camera/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key4},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err71];
}
else {
vErrors.push(err71);
}
errors++;
}
}
if(data34.source !== undefined){
if("device_camera" !== data34.source){
const err72 = {instancePath:instancePath+"/camera/source",schemaPath:"#/properties/camera/properties/source/const",keyword:"const",params:{allowedValue: "device_camera"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err72];
}
else {
vErrors.push(err72);
}
errors++;
}
}
if(data34.size !== undefined){
let data36 = data34.size;
if(!((data36 === "320x240") || (data36 === "640x480"))){
const err73 = {instancePath:instancePath+"/camera/size",schemaPath:"#/properties/camera/properties/size/enum",keyword:"enum",params:{allowedValues: schema31.properties.camera.properties.size.enum},message:"must be equal to one of the allowed values"};
if(vErrors === null){
vErrors = [err73];
}
else {
vErrors.push(err73);
}
errors++;
}
}
if(data34.fps !== undefined){
let data37 = data34.fps;
if(!((typeof data37 == "number") && (!(data37 % 1) && !isNaN(data37)))){
const err74 = {instancePath:instancePath+"/camera/fps",schemaPath:"#/properties/camera/properties/fps/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err74];
}
else {
vErrors.push(err74);
}
errors++;
}
if(typeof data37 == "number"){
if(data37 > 15 || isNaN(data37)){
const err75 = {instancePath:instancePath+"/camera/fps",schemaPath:"#/properties/camera/properties/fps/maximum",keyword:"maximum",params:{comparison: "<=", limit: 15},message:"must be <= 15"};
if(vErrors === null){
vErrors = [err75];
}
else {
vErrors.push(err75);
}
errors++;
}
if(data37 < 1 || isNaN(data37)){
const err76 = {instancePath:instancePath+"/camera/fps",schemaPath:"#/properties/camera/properties/fps/minimum",keyword:"minimum",params:{comparison: ">=", limit: 1},message:"must be >= 1"};
if(vErrors === null){
vErrors = [err76];
}
else {
vErrors.push(err76);
}
errors++;
}
}
}
}
else {
const err77 = {instancePath:instancePath+"/camera",schemaPath:"#/properties/camera/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err77];
}
else {
vErrors.push(err77);
}
errors++;
}
}
if(data.blocks !== undefined){
let data38 = data.blocks;
if(Array.isArray(data38)){
if(data38.length > 7){
const err78 = {instancePath:instancePath+"/blocks",schemaPath:"#/properties/blocks/maxItems",keyword:"maxItems",params:{limit: 7},message:"must NOT have more than 7 items"};
if(vErrors === null){
vErrors = [err78];
}
else {
vErrors.push(err78);
}
errors++;
}
if(data38.length < 2){
const err79 = {instancePath:instancePath+"/blocks",schemaPath:"#/properties/blocks/minItems",keyword:"minItems",params:{limit: 2},message:"must NOT have fewer than 2 items"};
if(vErrors === null){
vErrors = [err79];
}
else {
vErrors.push(err79);
}
errors++;
}
const len8 = data38.length;
if(len8 > 0){
if(!(validate21(data38[0], {instancePath:instancePath+"/blocks/0",parentData:data38,parentDataProperty:0,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate21.errors : vErrors.concat(validate21.errors);
errors = vErrors.length;
}
}
if(len8 > 1){
if(!(validate23(data38[1], {instancePath:instancePath+"/blocks/1",parentData:data38,parentDataProperty:1,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate23.errors : vErrors.concat(validate23.errors);
errors = vErrors.length;
}
}
const len9 = data38.length;
var valid49 = len9 <= 2;
if(!valid49){
for(let i8=2; i8<len9; i8++){
let data41 = data38[i8];
const _errs107 = errors;
const _errs108 = errors;
let valid50 = false;
let passing1 = null;
const _errs109 = errors;
if(data41 && typeof data41 == "object" && !Array.isArray(data41)){
if(data41.type === undefined){
const err80 = {instancePath:instancePath+"/blocks/" + i8,schemaPath:"#/$defs/color_finder/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err80];
}
else {
vErrors.push(err80);
}
errors++;
}
if(data41.settings === undefined){
const err81 = {instancePath:instancePath+"/blocks/" + i8,schemaPath:"#/$defs/color_finder/required",keyword:"required",params:{missingProperty: "settings"},message:"must have required property '"+"settings"+"'"};
if(vErrors === null){
vErrors = [err81];
}
else {
vErrors.push(err81);
}
errors++;
}
for(const key5 in data41){
if(!((key5 === "type") || (key5 === "settings"))){
const err82 = {instancePath:instancePath+"/blocks/" + i8,schemaPath:"#/$defs/color_finder/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key5},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err82];
}
else {
vErrors.push(err82);
}
errors++;
}
}
if(data41.type !== undefined){
if("color_finder" !== data41.type){
const err83 = {instancePath:instancePath+"/blocks/" + i8+"/type",schemaPath:"#/$defs/color_finder/properties/type/const",keyword:"const",params:{allowedValue: "color_finder"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err83];
}
else {
vErrors.push(err83);
}
errors++;
}
}
if(data41.settings !== undefined){
let data43 = data41.settings;
if(data43 && typeof data43 == "object" && !Array.isArray(data43)){
if(data43.hue_center === undefined){
const err84 = {instancePath:instancePath+"/blocks/" + i8+"/settings",schemaPath:"#/$defs/color_finder/properties/settings/required",keyword:"required",params:{missingProperty: "hue_center"},message:"must have required property '"+"hue_center"+"'"};
if(vErrors === null){
vErrors = [err84];
}
else {
vErrors.push(err84);
}
errors++;
}
if(data43.hue_half_width === undefined){
const err85 = {instancePath:instancePath+"/blocks/" + i8+"/settings",schemaPath:"#/$defs/color_finder/properties/settings/required",keyword:"required",params:{missingProperty: "hue_half_width"},message:"must have required property '"+"hue_half_width"+"'"};
if(vErrors === null){
vErrors = [err85];
}
else {
vErrors.push(err85);
}
errors++;
}
if(data43.saturation_min === undefined){
const err86 = {instancePath:instancePath+"/blocks/" + i8+"/settings",schemaPath:"#/$defs/color_finder/properties/settings/required",keyword:"required",params:{missingProperty: "saturation_min"},message:"must have required property '"+"saturation_min"+"'"};
if(vErrors === null){
vErrors = [err86];
}
else {
vErrors.push(err86);
}
errors++;
}
if(data43.value_min === undefined){
const err87 = {instancePath:instancePath+"/blocks/" + i8+"/settings",schemaPath:"#/$defs/color_finder/properties/settings/required",keyword:"required",params:{missingProperty: "value_min"},message:"must have required property '"+"value_min"+"'"};
if(vErrors === null){
vErrors = [err87];
}
else {
vErrors.push(err87);
}
errors++;
}
if(data43.min_area_ratio === undefined){
const err88 = {instancePath:instancePath+"/blocks/" + i8+"/settings",schemaPath:"#/$defs/color_finder/properties/settings/required",keyword:"required",params:{missingProperty: "min_area_ratio"},message:"must have required property '"+"min_area_ratio"+"'"};
if(vErrors === null){
vErrors = [err88];
}
else {
vErrors.push(err88);
}
errors++;
}
for(const key6 in data43){
if(!(((((key6 === "hue_center") || (key6 === "hue_half_width")) || (key6 === "saturation_min")) || (key6 === "value_min")) || (key6 === "min_area_ratio"))){
const err89 = {instancePath:instancePath+"/blocks/" + i8+"/settings",schemaPath:"#/$defs/color_finder/properties/settings/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key6},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err89];
}
else {
vErrors.push(err89);
}
errors++;
}
}
if(data43.hue_center !== undefined){
let data44 = data43.hue_center;
if(!((typeof data44 == "number") && (!(data44 % 1) && !isNaN(data44)))){
const err90 = {instancePath:instancePath+"/blocks/" + i8+"/settings/hue_center",schemaPath:"#/$defs/color_finder/properties/settings/properties/hue_center/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err90];
}
else {
vErrors.push(err90);
}
errors++;
}
if(typeof data44 == "number"){
if(data44 > 179 || isNaN(data44)){
const err91 = {instancePath:instancePath+"/blocks/" + i8+"/settings/hue_center",schemaPath:"#/$defs/color_finder/properties/settings/properties/hue_center/maximum",keyword:"maximum",params:{comparison: "<=", limit: 179},message:"must be <= 179"};
if(vErrors === null){
vErrors = [err91];
}
else {
vErrors.push(err91);
}
errors++;
}
if(data44 < 0 || isNaN(data44)){
const err92 = {instancePath:instancePath+"/blocks/" + i8+"/settings/hue_center",schemaPath:"#/$defs/color_finder/properties/settings/properties/hue_center/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err92];
}
else {
vErrors.push(err92);
}
errors++;
}
}
}
if(data43.hue_half_width !== undefined){
let data45 = data43.hue_half_width;
if(!((typeof data45 == "number") && (!(data45 % 1) && !isNaN(data45)))){
const err93 = {instancePath:instancePath+"/blocks/" + i8+"/settings/hue_half_width",schemaPath:"#/$defs/color_finder/properties/settings/properties/hue_half_width/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err93];
}
else {
vErrors.push(err93);
}
errors++;
}
if(typeof data45 == "number"){
if(data45 > 30 || isNaN(data45)){
const err94 = {instancePath:instancePath+"/blocks/" + i8+"/settings/hue_half_width",schemaPath:"#/$defs/color_finder/properties/settings/properties/hue_half_width/maximum",keyword:"maximum",params:{comparison: "<=", limit: 30},message:"must be <= 30"};
if(vErrors === null){
vErrors = [err94];
}
else {
vErrors.push(err94);
}
errors++;
}
if(data45 < 1 || isNaN(data45)){
const err95 = {instancePath:instancePath+"/blocks/" + i8+"/settings/hue_half_width",schemaPath:"#/$defs/color_finder/properties/settings/properties/hue_half_width/minimum",keyword:"minimum",params:{comparison: ">=", limit: 1},message:"must be >= 1"};
if(vErrors === null){
vErrors = [err95];
}
else {
vErrors.push(err95);
}
errors++;
}
}
}
if(data43.saturation_min !== undefined){
let data46 = data43.saturation_min;
if(!((typeof data46 == "number") && (!(data46 % 1) && !isNaN(data46)))){
const err96 = {instancePath:instancePath+"/blocks/" + i8+"/settings/saturation_min",schemaPath:"#/$defs/color_finder/properties/settings/properties/saturation_min/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err96];
}
else {
vErrors.push(err96);
}
errors++;
}
if(typeof data46 == "number"){
if(data46 > 255 || isNaN(data46)){
const err97 = {instancePath:instancePath+"/blocks/" + i8+"/settings/saturation_min",schemaPath:"#/$defs/color_finder/properties/settings/properties/saturation_min/maximum",keyword:"maximum",params:{comparison: "<=", limit: 255},message:"must be <= 255"};
if(vErrors === null){
vErrors = [err97];
}
else {
vErrors.push(err97);
}
errors++;
}
if(data46 < 50 || isNaN(data46)){
const err98 = {instancePath:instancePath+"/blocks/" + i8+"/settings/saturation_min",schemaPath:"#/$defs/color_finder/properties/settings/properties/saturation_min/minimum",keyword:"minimum",params:{comparison: ">=", limit: 50},message:"must be >= 50"};
if(vErrors === null){
vErrors = [err98];
}
else {
vErrors.push(err98);
}
errors++;
}
}
}
if(data43.value_min !== undefined){
let data47 = data43.value_min;
if(!((typeof data47 == "number") && (!(data47 % 1) && !isNaN(data47)))){
const err99 = {instancePath:instancePath+"/blocks/" + i8+"/settings/value_min",schemaPath:"#/$defs/color_finder/properties/settings/properties/value_min/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err99];
}
else {
vErrors.push(err99);
}
errors++;
}
if(typeof data47 == "number"){
if(data47 > 255 || isNaN(data47)){
const err100 = {instancePath:instancePath+"/blocks/" + i8+"/settings/value_min",schemaPath:"#/$defs/color_finder/properties/settings/properties/value_min/maximum",keyword:"maximum",params:{comparison: "<=", limit: 255},message:"must be <= 255"};
if(vErrors === null){
vErrors = [err100];
}
else {
vErrors.push(err100);
}
errors++;
}
if(data47 < 30 || isNaN(data47)){
const err101 = {instancePath:instancePath+"/blocks/" + i8+"/settings/value_min",schemaPath:"#/$defs/color_finder/properties/settings/properties/value_min/minimum",keyword:"minimum",params:{comparison: ">=", limit: 30},message:"must be >= 30"};
if(vErrors === null){
vErrors = [err101];
}
else {
vErrors.push(err101);
}
errors++;
}
}
}
if(data43.min_area_ratio !== undefined){
let data48 = data43.min_area_ratio;
if(typeof data48 == "number"){
if(data48 > 0.25 || isNaN(data48)){
const err102 = {instancePath:instancePath+"/blocks/" + i8+"/settings/min_area_ratio",schemaPath:"#/$defs/color_finder/properties/settings/properties/min_area_ratio/maximum",keyword:"maximum",params:{comparison: "<=", limit: 0.25},message:"must be <= 0.25"};
if(vErrors === null){
vErrors = [err102];
}
else {
vErrors.push(err102);
}
errors++;
}
if(data48 < 0.001 || isNaN(data48)){
const err103 = {instancePath:instancePath+"/blocks/" + i8+"/settings/min_area_ratio",schemaPath:"#/$defs/color_finder/properties/settings/properties/min_area_ratio/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0.001},message:"must be >= 0.001"};
if(vErrors === null){
vErrors = [err103];
}
else {
vErrors.push(err103);
}
errors++;
}
}
else {
const err104 = {instancePath:instancePath+"/blocks/" + i8+"/settings/min_area_ratio",schemaPath:"#/$defs/color_finder/properties/settings/properties/min_area_ratio/type",keyword:"type",params:{type: "number"},message:"must be number"};
if(vErrors === null){
vErrors = [err104];
}
else {
vErrors.push(err104);
}
errors++;
}
}
}
else {
const err105 = {instancePath:instancePath+"/blocks/" + i8+"/settings",schemaPath:"#/$defs/color_finder/properties/settings/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err105];
}
else {
vErrors.push(err105);
}
errors++;
}
}
}
else {
const err106 = {instancePath:instancePath+"/blocks/" + i8,schemaPath:"#/$defs/color_finder/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err106];
}
else {
vErrors.push(err106);
}
errors++;
}
var _valid4 = _errs109 === errors;
if(_valid4){
valid50 = true;
passing1 = 0;
var props4 = true;
}
const _errs127 = errors;
if(data41 && typeof data41 == "object" && !Array.isArray(data41)){
if(data41.type === undefined){
const err107 = {instancePath:instancePath+"/blocks/" + i8,schemaPath:"#/$defs/object_finder/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err107];
}
else {
vErrors.push(err107);
}
errors++;
}
if(data41.settings === undefined){
const err108 = {instancePath:instancePath+"/blocks/" + i8,schemaPath:"#/$defs/object_finder/required",keyword:"required",params:{missingProperty: "settings"},message:"must have required property '"+"settings"+"'"};
if(vErrors === null){
vErrors = [err108];
}
else {
vErrors.push(err108);
}
errors++;
}
for(const key7 in data41){
if(!((key7 === "type") || (key7 === "settings"))){
const err109 = {instancePath:instancePath+"/blocks/" + i8,schemaPath:"#/$defs/object_finder/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key7},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err109];
}
else {
vErrors.push(err109);
}
errors++;
}
}
if(data41.type !== undefined){
if("object_finder" !== data41.type){
const err110 = {instancePath:instancePath+"/blocks/" + i8+"/type",schemaPath:"#/$defs/object_finder/properties/type/const",keyword:"const",params:{allowedValue: "object_finder"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err110];
}
else {
vErrors.push(err110);
}
errors++;
}
}
if(data41.settings !== undefined){
let data50 = data41.settings;
if(data50 && typeof data50 == "object" && !Array.isArray(data50)){
if(data50.object === undefined){
const err111 = {instancePath:instancePath+"/blocks/" + i8+"/settings",schemaPath:"#/$defs/object_finder/properties/settings/required",keyword:"required",params:{missingProperty: "object"},message:"must have required property '"+"object"+"'"};
if(vErrors === null){
vErrors = [err111];
}
else {
vErrors.push(err111);
}
errors++;
}
if(data50.colour === undefined){
const err112 = {instancePath:instancePath+"/blocks/" + i8+"/settings",schemaPath:"#/$defs/object_finder/properties/settings/required",keyword:"required",params:{missingProperty: "colour"},message:"must have required property '"+"colour"+"'"};
if(vErrors === null){
vErrors = [err112];
}
else {
vErrors.push(err112);
}
errors++;
}
if(data50.min_confidence === undefined){
const err113 = {instancePath:instancePath+"/blocks/" + i8+"/settings",schemaPath:"#/$defs/object_finder/properties/settings/required",keyword:"required",params:{missingProperty: "min_confidence"},message:"must have required property '"+"min_confidence"+"'"};
if(vErrors === null){
vErrors = [err113];
}
else {
vErrors.push(err113);
}
errors++;
}
for(const key8 in data50){
if(!(((key8 === "object") || (key8 === "colour")) || (key8 === "min_confidence"))){
const err114 = {instancePath:instancePath+"/blocks/" + i8+"/settings",schemaPath:"#/$defs/object_finder/properties/settings/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key8},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err114];
}
else {
vErrors.push(err114);
}
errors++;
}
}
if(data50.object !== undefined){
let data51 = data50.object;
if(!(((((((((((((((((((((((data51 === "cell phone") || (data51 === "backpack")) || (data51 === "handbag")) || (data51 === "suitcase")) || (data51 === "umbrella")) || (data51 === "bottle")) || (data51 === "cup")) || (data51 === "bowl")) || (data51 === "laptop")) || (data51 === "keyboard")) || (data51 === "mouse")) || (data51 === "remote")) || (data51 === "book")) || (data51 === "clock")) || (data51 === "chair")) || (data51 === "scissors")) || (data51 === "teddy bear")) || (data51 === "apple")) || (data51 === "banana")) || (data51 === "tv")) || (data51 === "vase")) || (data51 === "potted plant")) || (data51 === "bicycle"))){
const err115 = {instancePath:instancePath+"/blocks/" + i8+"/settings/object",schemaPath:"#/$defs/object_finder/properties/settings/properties/object/enum",keyword:"enum",params:{allowedValues: schema48.properties.settings.properties.object.enum},message:"must be equal to one of the allowed values"};
if(vErrors === null){
vErrors = [err115];
}
else {
vErrors.push(err115);
}
errors++;
}
}
if(data50.colour !== undefined){
let data52 = data50.colour;
if(!((((((((((data52 === "any") || (data52 === "red")) || (data52 === "orange")) || (data52 === "yellow")) || (data52 === "green")) || (data52 === "blue")) || (data52 === "purple")) || (data52 === "white")) || (data52 === "black")) || (data52 === "grey"))){
const err116 = {instancePath:instancePath+"/blocks/" + i8+"/settings/colour",schemaPath:"#/$defs/object_finder/properties/settings/properties/colour/enum",keyword:"enum",params:{allowedValues: schema48.properties.settings.properties.colour.enum},message:"must be equal to one of the allowed values"};
if(vErrors === null){
vErrors = [err116];
}
else {
vErrors.push(err116);
}
errors++;
}
}
if(data50.min_confidence !== undefined){
let data53 = data50.min_confidence;
if(typeof data53 == "number"){
if(data53 > 0.95 || isNaN(data53)){
const err117 = {instancePath:instancePath+"/blocks/" + i8+"/settings/min_confidence",schemaPath:"#/$defs/object_finder/properties/settings/properties/min_confidence/maximum",keyword:"maximum",params:{comparison: "<=", limit: 0.95},message:"must be <= 0.95"};
if(vErrors === null){
vErrors = [err117];
}
else {
vErrors.push(err117);
}
errors++;
}
if(data53 < 0.3 || isNaN(data53)){
const err118 = {instancePath:instancePath+"/blocks/" + i8+"/settings/min_confidence",schemaPath:"#/$defs/object_finder/properties/settings/properties/min_confidence/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0.3},message:"must be >= 0.3"};
if(vErrors === null){
vErrors = [err118];
}
else {
vErrors.push(err118);
}
errors++;
}
}
else {
const err119 = {instancePath:instancePath+"/blocks/" + i8+"/settings/min_confidence",schemaPath:"#/$defs/object_finder/properties/settings/properties/min_confidence/type",keyword:"type",params:{type: "number"},message:"must be number"};
if(vErrors === null){
vErrors = [err119];
}
else {
vErrors.push(err119);
}
errors++;
}
}
}
else {
const err120 = {instancePath:instancePath+"/blocks/" + i8+"/settings",schemaPath:"#/$defs/object_finder/properties/settings/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err120];
}
else {
vErrors.push(err120);
}
errors++;
}
}
}
else {
const err121 = {instancePath:instancePath+"/blocks/" + i8,schemaPath:"#/$defs/object_finder/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err121];
}
else {
vErrors.push(err121);
}
errors++;
}
var _valid4 = _errs127 === errors;
if(_valid4 && valid50){
valid50 = false;
passing1 = [passing1, 1];
}
else {
if(_valid4){
valid50 = true;
passing1 = 1;
if(props4 !== true){
props4 = true;
}
}
const _errs140 = errors;
if(!(validate29(data41, {instancePath:instancePath+"/blocks/" + i8,parentData:data38,parentDataProperty:i8,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate29.errors : vErrors.concat(validate29.errors);
errors = vErrors.length;
}
var _valid4 = _errs140 === errors;
if(_valid4 && valid50){
valid50 = false;
passing1 = [passing1, 2];
}
else {
if(_valid4){
valid50 = true;
passing1 = 2;
if(props4 !== true){
props4 = true;
}
}
const _errs141 = errors;
if(data41 && typeof data41 == "object" && !Array.isArray(data41)){
if(data41.type === undefined){
const err122 = {instancePath:instancePath+"/blocks/" + i8,schemaPath:"#/$defs/person_detector/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err122];
}
else {
vErrors.push(err122);
}
errors++;
}
if(data41.settings === undefined){
const err123 = {instancePath:instancePath+"/blocks/" + i8,schemaPath:"#/$defs/person_detector/required",keyword:"required",params:{missingProperty: "settings"},message:"must have required property '"+"settings"+"'"};
if(vErrors === null){
vErrors = [err123];
}
else {
vErrors.push(err123);
}
errors++;
}
for(const key9 in data41){
if(!((key9 === "type") || (key9 === "settings"))){
const err124 = {instancePath:instancePath+"/blocks/" + i8,schemaPath:"#/$defs/person_detector/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key9},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err124];
}
else {
vErrors.push(err124);
}
errors++;
}
}
if(data41.type !== undefined){
if("person_detector" !== data41.type){
const err125 = {instancePath:instancePath+"/blocks/" + i8+"/type",schemaPath:"#/$defs/person_detector/properties/type/const",keyword:"const",params:{allowedValue: "person_detector"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err125];
}
else {
vErrors.push(err125);
}
errors++;
}
}
if(data41.settings !== undefined){
let data55 = data41.settings;
if(data55 && typeof data55 == "object" && !Array.isArray(data55)){
if(data55.min_confidence === undefined){
const err126 = {instancePath:instancePath+"/blocks/" + i8+"/settings",schemaPath:"#/$defs/person_detector/properties/settings/required",keyword:"required",params:{missingProperty: "min_confidence"},message:"must have required property '"+"min_confidence"+"'"};
if(vErrors === null){
vErrors = [err126];
}
else {
vErrors.push(err126);
}
errors++;
}
for(const key10 in data55){
if(!(key10 === "min_confidence")){
const err127 = {instancePath:instancePath+"/blocks/" + i8+"/settings",schemaPath:"#/$defs/person_detector/properties/settings/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key10},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err127];
}
else {
vErrors.push(err127);
}
errors++;
}
}
if(data55.min_confidence !== undefined){
let data56 = data55.min_confidence;
if(typeof data56 == "number"){
if(data56 > 0.95 || isNaN(data56)){
const err128 = {instancePath:instancePath+"/blocks/" + i8+"/settings/min_confidence",schemaPath:"#/$defs/person_detector/properties/settings/properties/min_confidence/maximum",keyword:"maximum",params:{comparison: "<=", limit: 0.95},message:"must be <= 0.95"};
if(vErrors === null){
vErrors = [err128];
}
else {
vErrors.push(err128);
}
errors++;
}
if(data56 < 0.3 || isNaN(data56)){
const err129 = {instancePath:instancePath+"/blocks/" + i8+"/settings/min_confidence",schemaPath:"#/$defs/person_detector/properties/settings/properties/min_confidence/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0.3},message:"must be >= 0.3"};
if(vErrors === null){
vErrors = [err129];
}
else {
vErrors.push(err129);
}
errors++;
}
}
else {
const err130 = {instancePath:instancePath+"/blocks/" + i8+"/settings/min_confidence",schemaPath:"#/$defs/person_detector/properties/settings/properties/min_confidence/type",keyword:"type",params:{type: "number"},message:"must be number"};
if(vErrors === null){
vErrors = [err130];
}
else {
vErrors.push(err130);
}
errors++;
}
}
}
else {
const err131 = {instancePath:instancePath+"/blocks/" + i8+"/settings",schemaPath:"#/$defs/person_detector/properties/settings/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err131];
}
else {
vErrors.push(err131);
}
errors++;
}
}
}
else {
const err132 = {instancePath:instancePath+"/blocks/" + i8,schemaPath:"#/$defs/person_detector/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err132];
}
else {
vErrors.push(err132);
}
errors++;
}
var _valid4 = _errs141 === errors;
if(_valid4 && valid50){
valid50 = false;
passing1 = [passing1, 3];
}
else {
if(_valid4){
valid50 = true;
passing1 = 3;
if(props4 !== true){
props4 = true;
}
}
const _errs151 = errors;
if(!(validate25(data41, {instancePath:instancePath+"/blocks/" + i8,parentData:data38,parentDataProperty:i8,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate25.errors : vErrors.concat(validate25.errors);
errors = vErrors.length;
}
var _valid4 = _errs151 === errors;
if(_valid4 && valid50){
valid50 = false;
passing1 = [passing1, 4];
}
else {
if(_valid4){
valid50 = true;
passing1 = 4;
if(props4 !== true){
props4 = true;
}
}
const _errs152 = errors;
if(data41 && typeof data41 == "object" && !Array.isArray(data41)){
if(data41.type === undefined){
const err133 = {instancePath:instancePath+"/blocks/" + i8,schemaPath:"#/$defs/looming/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err133];
}
else {
vErrors.push(err133);
}
errors++;
}
if(data41.settings === undefined){
const err134 = {instancePath:instancePath+"/blocks/" + i8,schemaPath:"#/$defs/looming/required",keyword:"required",params:{missingProperty: "settings"},message:"must have required property '"+"settings"+"'"};
if(vErrors === null){
vErrors = [err134];
}
else {
vErrors.push(err134);
}
errors++;
}
for(const key11 in data41){
if(!((key11 === "type") || (key11 === "settings"))){
const err135 = {instancePath:instancePath+"/blocks/" + i8,schemaPath:"#/$defs/looming/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key11},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err135];
}
else {
vErrors.push(err135);
}
errors++;
}
}
if(data41.type !== undefined){
if("looming" !== data41.type){
const err136 = {instancePath:instancePath+"/blocks/" + i8+"/type",schemaPath:"#/$defs/looming/properties/type/const",keyword:"const",params:{allowedValue: "looming"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err136];
}
else {
vErrors.push(err136);
}
errors++;
}
}
if(data41.settings !== undefined){
let data58 = data41.settings;
if(data58 && typeof data58 == "object" && !Array.isArray(data58)){
if(data58.min_expansion_per_second === undefined){
const err137 = {instancePath:instancePath+"/blocks/" + i8+"/settings",schemaPath:"#/$defs/looming/properties/settings/required",keyword:"required",params:{missingProperty: "min_expansion_per_second"},message:"must have required property '"+"min_expansion_per_second"+"'"};
if(vErrors === null){
vErrors = [err137];
}
else {
vErrors.push(err137);
}
errors++;
}
for(const key12 in data58){
if(!(key12 === "min_expansion_per_second")){
const err138 = {instancePath:instancePath+"/blocks/" + i8+"/settings",schemaPath:"#/$defs/looming/properties/settings/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key12},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err138];
}
else {
vErrors.push(err138);
}
errors++;
}
}
if(data58.min_expansion_per_second !== undefined){
let data59 = data58.min_expansion_per_second;
if(typeof data59 == "number"){
if(data59 > 5 || isNaN(data59)){
const err139 = {instancePath:instancePath+"/blocks/" + i8+"/settings/min_expansion_per_second",schemaPath:"#/$defs/looming/properties/settings/properties/min_expansion_per_second/maximum",keyword:"maximum",params:{comparison: "<=", limit: 5},message:"must be <= 5"};
if(vErrors === null){
vErrors = [err139];
}
else {
vErrors.push(err139);
}
errors++;
}
if(data59 < 0.1 || isNaN(data59)){
const err140 = {instancePath:instancePath+"/blocks/" + i8+"/settings/min_expansion_per_second",schemaPath:"#/$defs/looming/properties/settings/properties/min_expansion_per_second/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0.1},message:"must be >= 0.1"};
if(vErrors === null){
vErrors = [err140];
}
else {
vErrors.push(err140);
}
errors++;
}
}
else {
const err141 = {instancePath:instancePath+"/blocks/" + i8+"/settings/min_expansion_per_second",schemaPath:"#/$defs/looming/properties/settings/properties/min_expansion_per_second/type",keyword:"type",params:{type: "number"},message:"must be number"};
if(vErrors === null){
vErrors = [err141];
}
else {
vErrors.push(err141);
}
errors++;
}
}
}
else {
const err142 = {instancePath:instancePath+"/blocks/" + i8+"/settings",schemaPath:"#/$defs/looming/properties/settings/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err142];
}
else {
vErrors.push(err142);
}
errors++;
}
}
}
else {
const err143 = {instancePath:instancePath+"/blocks/" + i8,schemaPath:"#/$defs/looming/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err143];
}
else {
vErrors.push(err143);
}
errors++;
}
var _valid4 = _errs152 === errors;
if(_valid4 && valid50){
valid50 = false;
passing1 = [passing1, 5];
}
else {
if(_valid4){
valid50 = true;
passing1 = 5;
if(props4 !== true){
props4 = true;
}
}
}
}
}
}
}
if(!valid50){
const err144 = {instancePath:instancePath+"/blocks/" + i8,schemaPath:"#/properties/blocks/items/oneOf",keyword:"oneOf",params:{passingSchemas: passing1},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err144];
}
else {
vErrors.push(err144);
}
errors++;
}
else {
errors = _errs108;
if(vErrors !== null){
if(_errs108){
vErrors.length = _errs108;
}
else {
vErrors = null;
}
}
}
var valid49 = _errs107 === errors;
}
}
}
else {
const err145 = {instancePath:instancePath+"/blocks",schemaPath:"#/properties/blocks/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err145];
}
else {
vErrors.push(err145);
}
errors++;
}
}
if(data.brain !== undefined){
let data60 = data.brain;
const _errs164 = errors;
let valid63 = false;
let passing2 = null;
const _errs165 = errors;
if(data60 && typeof data60 == "object" && !Array.isArray(data60)){
if(data60.type === undefined){
const err146 = {instancePath:instancePath+"/brain",schemaPath:"#/$defs/brain_none/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err146];
}
else {
vErrors.push(err146);
}
errors++;
}
for(const key13 in data60){
if(!(key13 === "type")){
const err147 = {instancePath:instancePath+"/brain",schemaPath:"#/$defs/brain_none/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key13},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err147];
}
else {
vErrors.push(err147);
}
errors++;
}
}
if(data60.type !== undefined){
if("none" !== data60.type){
const err148 = {instancePath:instancePath+"/brain/type",schemaPath:"#/$defs/brain_none/properties/type/const",keyword:"const",params:{allowedValue: "none"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err148];
}
else {
vErrors.push(err148);
}
errors++;
}
}
}
else {
const err149 = {instancePath:instancePath+"/brain",schemaPath:"#/$defs/brain_none/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err149];
}
else {
vErrors.push(err149);
}
errors++;
}
var _valid5 = _errs165 === errors;
if(_valid5){
valid63 = true;
passing2 = 0;
var props5 = true;
}
const _errs170 = errors;
if(data60 && typeof data60 == "object" && !Array.isArray(data60)){
if(data60.type === undefined){
const err150 = {instancePath:instancePath+"/brain",schemaPath:"#/$defs/brain_flybrain/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err150];
}
else {
vErrors.push(err150);
}
errors++;
}
if(data60.settings === undefined){
const err151 = {instancePath:instancePath+"/brain",schemaPath:"#/$defs/brain_flybrain/required",keyword:"required",params:{missingProperty: "settings"},message:"must have required property '"+"settings"+"'"};
if(vErrors === null){
vErrors = [err151];
}
else {
vErrors.push(err151);
}
errors++;
}
for(const key14 in data60){
if(!((key14 === "type") || (key14 === "settings"))){
const err152 = {instancePath:instancePath+"/brain",schemaPath:"#/$defs/brain_flybrain/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key14},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err152];
}
else {
vErrors.push(err152);
}
errors++;
}
}
if(data60.type !== undefined){
if("flybrain" !== data60.type){
const err153 = {instancePath:instancePath+"/brain/type",schemaPath:"#/$defs/brain_flybrain/properties/type/const",keyword:"const",params:{allowedValue: "flybrain"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err153];
}
else {
vErrors.push(err153);
}
errors++;
}
}
if(data60.settings !== undefined){
let data63 = data60.settings;
if(data63 && typeof data63 == "object" && !Array.isArray(data63)){
if(data63.turn_gain === undefined){
const err154 = {instancePath:instancePath+"/brain/settings",schemaPath:"#/$defs/brain_flybrain/properties/settings/required",keyword:"required",params:{missingProperty: "turn_gain"},message:"must have required property '"+"turn_gain"+"'"};
if(vErrors === null){
vErrors = [err154];
}
else {
vErrors.push(err154);
}
errors++;
}
if(data63.deadband === undefined){
const err155 = {instancePath:instancePath+"/brain/settings",schemaPath:"#/$defs/brain_flybrain/properties/settings/required",keyword:"required",params:{missingProperty: "deadband"},message:"must have required property '"+"deadband"+"'"};
if(vErrors === null){
vErrors = [err155];
}
else {
vErrors.push(err155);
}
errors++;
}
for(const key15 in data63){
if(!((key15 === "turn_gain") || (key15 === "deadband"))){
const err156 = {instancePath:instancePath+"/brain/settings",schemaPath:"#/$defs/brain_flybrain/properties/settings/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key15},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err156];
}
else {
vErrors.push(err156);
}
errors++;
}
}
if(data63.turn_gain !== undefined){
let data64 = data63.turn_gain;
if(typeof data64 == "number"){
if(data64 > 2 || isNaN(data64)){
const err157 = {instancePath:instancePath+"/brain/settings/turn_gain",schemaPath:"#/$defs/brain_flybrain/properties/settings/properties/turn_gain/maximum",keyword:"maximum",params:{comparison: "<=", limit: 2},message:"must be <= 2"};
if(vErrors === null){
vErrors = [err157];
}
else {
vErrors.push(err157);
}
errors++;
}
if(data64 < 0.1 || isNaN(data64)){
const err158 = {instancePath:instancePath+"/brain/settings/turn_gain",schemaPath:"#/$defs/brain_flybrain/properties/settings/properties/turn_gain/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0.1},message:"must be >= 0.1"};
if(vErrors === null){
vErrors = [err158];
}
else {
vErrors.push(err158);
}
errors++;
}
}
else {
const err159 = {instancePath:instancePath+"/brain/settings/turn_gain",schemaPath:"#/$defs/brain_flybrain/properties/settings/properties/turn_gain/type",keyword:"type",params:{type: "number"},message:"must be number"};
if(vErrors === null){
vErrors = [err159];
}
else {
vErrors.push(err159);
}
errors++;
}
}
if(data63.deadband !== undefined){
let data65 = data63.deadband;
if(typeof data65 == "number"){
if(data65 > 0.25 || isNaN(data65)){
const err160 = {instancePath:instancePath+"/brain/settings/deadband",schemaPath:"#/$defs/brain_flybrain/properties/settings/properties/deadband/maximum",keyword:"maximum",params:{comparison: "<=", limit: 0.25},message:"must be <= 0.25"};
if(vErrors === null){
vErrors = [err160];
}
else {
vErrors.push(err160);
}
errors++;
}
if(data65 < 0.02 || isNaN(data65)){
const err161 = {instancePath:instancePath+"/brain/settings/deadband",schemaPath:"#/$defs/brain_flybrain/properties/settings/properties/deadband/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0.02},message:"must be >= 0.02"};
if(vErrors === null){
vErrors = [err161];
}
else {
vErrors.push(err161);
}
errors++;
}
}
else {
const err162 = {instancePath:instancePath+"/brain/settings/deadband",schemaPath:"#/$defs/brain_flybrain/properties/settings/properties/deadband/type",keyword:"type",params:{type: "number"},message:"must be number"};
if(vErrors === null){
vErrors = [err162];
}
else {
vErrors.push(err162);
}
errors++;
}
}
}
else {
const err163 = {instancePath:instancePath+"/brain/settings",schemaPath:"#/$defs/brain_flybrain/properties/settings/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err163];
}
else {
vErrors.push(err163);
}
errors++;
}
}
}
else {
const err164 = {instancePath:instancePath+"/brain",schemaPath:"#/$defs/brain_flybrain/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err164];
}
else {
vErrors.push(err164);
}
errors++;
}
var _valid5 = _errs170 === errors;
if(_valid5 && valid63){
valid63 = false;
passing2 = [passing2, 1];
}
else {
if(_valid5){
valid63 = true;
passing2 = 1;
if(props5 !== true){
props5 = true;
}
}
}
if(!valid63){
const err165 = {instancePath:instancePath+"/brain",schemaPath:"#/properties/brain/oneOf",keyword:"oneOf",params:{passingSchemas: passing2},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err165];
}
else {
vErrors.push(err165);
}
errors++;
}
else {
errors = _errs164;
if(vErrors !== null){
if(_errs164){
vErrors.length = _errs164;
}
else {
vErrors = null;
}
}
}
}
if(data.actions !== undefined){
let data66 = data.actions;
if(Array.isArray(data66)){
if(data66.length > 2){
const err166 = {instancePath:instancePath+"/actions",schemaPath:"#/properties/actions/maxItems",keyword:"maxItems",params:{limit: 2},message:"must NOT have more than 2 items"};
if(vErrors === null){
vErrors = [err166];
}
else {
vErrors.push(err166);
}
errors++;
}
if(data66.length < 1){
const err167 = {instancePath:instancePath+"/actions",schemaPath:"#/properties/actions/minItems",keyword:"minItems",params:{limit: 1},message:"must NOT have fewer than 1 items"};
if(vErrors === null){
vErrors = [err167];
}
else {
vErrors.push(err167);
}
errors++;
}
const len10 = data66.length;
if(len10 > 0){
let data67 = data66[0];
if(data67 && typeof data67 == "object" && !Array.isArray(data67)){
if(data67.type === undefined){
const err168 = {instancePath:instancePath+"/actions/0",schemaPath:"#/properties/actions/prefixItems/0/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err168];
}
else {
vErrors.push(err168);
}
errors++;
}
for(const key16 in data67){
if(!(key16 === "type")){
const err169 = {instancePath:instancePath+"/actions/0",schemaPath:"#/properties/actions/prefixItems/0/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key16},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err169];
}
else {
vErrors.push(err169);
}
errors++;
}
}
if(data67.type !== undefined){
if("dashboard" !== data67.type){
const err170 = {instancePath:instancePath+"/actions/0/type",schemaPath:"#/properties/actions/prefixItems/0/properties/type/const",keyword:"const",params:{allowedValue: "dashboard"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err170];
}
else {
vErrors.push(err170);
}
errors++;
}
}
}
else {
const err171 = {instancePath:instancePath+"/actions/0",schemaPath:"#/properties/actions/prefixItems/0/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err171];
}
else {
vErrors.push(err171);
}
errors++;
}
}
const len11 = data66.length;
var valid71 = len11 <= 1;
if(!valid71){
for(let i9=1; i9<len11; i9++){
let data69 = data66[i9];
const _errs189 = errors;
const _errs190 = errors;
let valid72 = false;
let passing3 = null;
const _errs191 = errors;
if(data69 && typeof data69 == "object" && !Array.isArray(data69)){
if(data69.type === undefined){
const err172 = {instancePath:instancePath+"/actions/" + i9,schemaPath:"#/$defs/alert/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err172];
}
else {
vErrors.push(err172);
}
errors++;
}
if(data69.template === undefined){
const err173 = {instancePath:instancePath+"/actions/" + i9,schemaPath:"#/$defs/alert/required",keyword:"required",params:{missingProperty: "template"},message:"must have required property '"+"template"+"'"};
if(vErrors === null){
vErrors = [err173];
}
else {
vErrors.push(err173);
}
errors++;
}
for(const key17 in data69){
if(!((key17 === "type") || (key17 === "template"))){
const err174 = {instancePath:instancePath+"/actions/" + i9,schemaPath:"#/$defs/alert/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key17},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err174];
}
else {
vErrors.push(err174);
}
errors++;
}
}
if(data69.type !== undefined){
if("alert" !== data69.type){
const err175 = {instancePath:instancePath+"/actions/" + i9+"/type",schemaPath:"#/$defs/alert/properties/type/const",keyword:"const",params:{allowedValue: "alert"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err175];
}
else {
vErrors.push(err175);
}
errors++;
}
}
if(data69.template !== undefined){
let data71 = data69.template;
if(!((data71 === "motion_detected") || (data71 === "count_changed"))){
const err176 = {instancePath:instancePath+"/actions/" + i9+"/template",schemaPath:"#/$defs/alert/properties/template/enum",keyword:"enum",params:{allowedValues: schema55.properties.template.enum},message:"must be equal to one of the allowed values"};
if(vErrors === null){
vErrors = [err176];
}
else {
vErrors.push(err176);
}
errors++;
}
}
}
else {
const err177 = {instancePath:instancePath+"/actions/" + i9,schemaPath:"#/$defs/alert/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err177];
}
else {
vErrors.push(err177);
}
errors++;
}
var _valid6 = _errs191 === errors;
if(_valid6){
valid72 = true;
passing3 = 0;
var props6 = true;
}
const _errs198 = errors;
if(data69 && typeof data69 == "object" && !Array.isArray(data69)){
if(data69.type === undefined){
const err178 = {instancePath:instancePath+"/actions/" + i9,schemaPath:"#/$defs/motors/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err178];
}
else {
vErrors.push(err178);
}
errors++;
}
if(data69.max_speed_ratio === undefined){
const err179 = {instancePath:instancePath+"/actions/" + i9,schemaPath:"#/$defs/motors/required",keyword:"required",params:{missingProperty: "max_speed_ratio"},message:"must have required property '"+"max_speed_ratio"+"'"};
if(vErrors === null){
vErrors = [err179];
}
else {
vErrors.push(err179);
}
errors++;
}
for(const key18 in data69){
if(!((key18 === "type") || (key18 === "max_speed_ratio"))){
const err180 = {instancePath:instancePath+"/actions/" + i9,schemaPath:"#/$defs/motors/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key18},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err180];
}
else {
vErrors.push(err180);
}
errors++;
}
}
if(data69.type !== undefined){
if("motors" !== data69.type){
const err181 = {instancePath:instancePath+"/actions/" + i9+"/type",schemaPath:"#/$defs/motors/properties/type/const",keyword:"const",params:{allowedValue: "motors"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err181];
}
else {
vErrors.push(err181);
}
errors++;
}
}
if(data69.max_speed_ratio !== undefined){
let data73 = data69.max_speed_ratio;
if(typeof data73 == "number"){
if(data73 > 0.25 || isNaN(data73)){
const err182 = {instancePath:instancePath+"/actions/" + i9+"/max_speed_ratio",schemaPath:"#/$defs/motors/properties/max_speed_ratio/maximum",keyword:"maximum",params:{comparison: "<=", limit: 0.25},message:"must be <= 0.25"};
if(vErrors === null){
vErrors = [err182];
}
else {
vErrors.push(err182);
}
errors++;
}
if(data73 < 0.05 || isNaN(data73)){
const err183 = {instancePath:instancePath+"/actions/" + i9+"/max_speed_ratio",schemaPath:"#/$defs/motors/properties/max_speed_ratio/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0.05},message:"must be >= 0.05"};
if(vErrors === null){
vErrors = [err183];
}
else {
vErrors.push(err183);
}
errors++;
}
}
else {
const err184 = {instancePath:instancePath+"/actions/" + i9+"/max_speed_ratio",schemaPath:"#/$defs/motors/properties/max_speed_ratio/type",keyword:"type",params:{type: "number"},message:"must be number"};
if(vErrors === null){
vErrors = [err184];
}
else {
vErrors.push(err184);
}
errors++;
}
}
}
else {
const err185 = {instancePath:instancePath+"/actions/" + i9,schemaPath:"#/$defs/motors/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err185];
}
else {
vErrors.push(err185);
}
errors++;
}
var _valid6 = _errs198 === errors;
if(_valid6 && valid72){
valid72 = false;
passing3 = [passing3, 1];
}
else {
if(_valid6){
valid72 = true;
passing3 = 1;
if(props6 !== true){
props6 = true;
}
}
}
if(!valid72){
const err186 = {instancePath:instancePath+"/actions/" + i9,schemaPath:"#/properties/actions/items/oneOf",keyword:"oneOf",params:{passingSchemas: passing3},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err186];
}
else {
vErrors.push(err186);
}
errors++;
}
else {
errors = _errs190;
if(vErrors !== null){
if(_errs190){
vErrors.length = _errs190;
}
else {
vErrors = null;
}
}
}
var valid71 = _errs189 === errors;
}
}
}
else {
const err187 = {instancePath:instancePath+"/actions",schemaPath:"#/properties/actions/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err187];
}
else {
vErrors.push(err187);
}
errors++;
}
}
if(data.privacy !== undefined){
let data74 = data.privacy;
if(data74 && typeof data74 == "object" && !Array.isArray(data74)){
if(data74.school === undefined){
const err188 = {instancePath:instancePath+"/privacy",schemaPath:"#/properties/privacy/required",keyword:"required",params:{missingProperty: "school"},message:"must have required property '"+"school"+"'"};
if(vErrors === null){
vErrors = [err188];
}
else {
vErrors.push(err188);
}
errors++;
}
for(const key19 in data74){
if(!(key19 === "school")){
const err189 = {instancePath:instancePath+"/privacy",schemaPath:"#/properties/privacy/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key19},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err189];
}
else {
vErrors.push(err189);
}
errors++;
}
}
if(data74.school !== undefined){
if(typeof data74.school !== "boolean"){
const err190 = {instancePath:instancePath+"/privacy/school",schemaPath:"#/properties/privacy/properties/school/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err190];
}
else {
vErrors.push(err190);
}
errors++;
}
}
}
else {
const err191 = {instancePath:instancePath+"/privacy",schemaPath:"#/properties/privacy/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err191];
}
else {
vErrors.push(err191);
}
errors++;
}
}
}
else {
const err192 = {instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err192];
}
else {
vErrors.push(err192);
}
errors++;
}
validate20.errors = vErrors;
return errors === 0;
}
validate20.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

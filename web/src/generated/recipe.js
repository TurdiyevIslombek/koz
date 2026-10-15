// Generated from contracts/recipe.schema.json. Do not hand-edit.
import ajvEqual from 'ajv/dist/runtime/equal.js';
"use strict";
export const validate = validate20;
export default validate20;
const schema31 = {"$schema":"https://json-schema.org/draft/2020-12/schema","title":"Ko'z recipe, version 1","$comment":"Structural check only. contracts/events.md section 3 lists the extra checks the runner must also make. A recipe never holds device setup (camera address, ownership, allowed area, motor arming).","type":"object","additionalProperties":false,"required":["version","language","camera","blocks","brain","actions","privacy"],"properties":{"version":{"const":1},"language":{"enum":["uz","ru","en"]},"camera":{"type":"object","additionalProperties":false,"required":["source","size","fps"],"properties":{"source":{"const":"device_camera"},"size":{"enum":["320x240","640x480"]},"fps":{"type":"integer","minimum":1,"maximum":15}}},"blocks":{"type":"array","minItems":2,"maxItems":7,"prefixItems":[{"$ref":"#/$defs/privacy_guard"},{"$ref":"#/$defs/face_blur"}],"items":{"oneOf":[{"$ref":"#/$defs/color_finder"},{"$ref":"#/$defs/motion_zone"},{"$ref":"#/$defs/person_detector"},{"$ref":"#/$defs/line_counter"},{"$ref":"#/$defs/looming"}]}},"brain":{"oneOf":[{"$ref":"#/$defs/brain_none"},{"$ref":"#/$defs/brain_flybrain"}]},"actions":{"type":"array","minItems":1,"maxItems":2,"prefixItems":[{"type":"object","additionalProperties":false,"required":["type"],"properties":{"type":{"const":"dashboard"}}}],"items":{"oneOf":[{"$ref":"#/$defs/alert"},{"$ref":"#/$defs/motors"}]}},"privacy":{"type":"object","additionalProperties":false,"required":["school"],"properties":{"school":{"type":"boolean"}}}},"allOf":[{"$comment":"Rule 6: school mode allows counting only.","if":{"required":["privacy"],"properties":{"privacy":{"required":["school"],"properties":{"school":{"const":true}}}}},"then":{"properties":{"brain":{"$ref":"#/$defs/brain_none"},"blocks":{"items":{"oneOf":[{"$ref":"#/$defs/privacy_guard"},{"$ref":"#/$defs/face_blur"},{"$ref":"#/$defs/person_detector"},{"$ref":"#/$defs/line_counter"}]}},"actions":{"const":[{"type":"dashboard"}]}}}},{"$comment":"Rule 11: motors only with the fly brain, and the fly brain only reads color_finder.","if":{"required":["brain"],"properties":{"brain":{"required":["type"],"properties":{"type":{"const":"flybrain"}}}}},"then":{"properties":{"blocks":{"contains":{"$ref":"#/$defs/is_color_finder"}},"actions":{"contains":{"$ref":"#/$defs/is_motors"}}}},"else":{"properties":{"actions":{"not":{"contains":{"$ref":"#/$defs/is_motors"}}}}}},{"$comment":"line_counter counts person_detector results.","if":{"required":["blocks"],"properties":{"blocks":{"contains":{"$ref":"#/$defs/is_line_counter"}}}},"then":{"properties":{"blocks":{"contains":{"$ref":"#/$defs/is_person_detector"}}}}}],"$defs":{"point":{"type":"array","minItems":2,"maxItems":2,"items":{"type":"number","minimum":0,"maximum":1}},"rect":{"$comment":"[left, top, right, bottom], normalized 0..1; left < right and top < bottom are checked by the runner.","type":"array","minItems":4,"maxItems":4,"items":{"type":"number","minimum":0,"maximum":1}},"no_settings":{"type":"object","additionalProperties":false,"maxProperties":0},"privacy_guard":{"$comment":"Locked: fixed code policy, nothing to tune.","type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"privacy_guard"},"settings":{"$ref":"#/$defs/no_settings"}}},"face_blur":{"$comment":"Locked: fixed code policy, nothing to tune.","type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"face_blur"},"settings":{"$ref":"#/$defs/no_settings"}}},"color_finder":{"type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"color_finder"},"settings":{"type":"object","additionalProperties":false,"required":["hue_center","hue_half_width","saturation_min","value_min","min_area_ratio"],"properties":{"hue_center":{"type":"integer","minimum":0,"maximum":179},"hue_half_width":{"type":"integer","minimum":1,"maximum":30},"saturation_min":{"type":"integer","minimum":50,"maximum":255},"value_min":{"type":"integer","minimum":30,"maximum":255},"min_area_ratio":{"type":"number","minimum":0.001,"maximum":0.25}}}}},"motion_zone":{"type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"motion_zone"},"settings":{"type":"object","additionalProperties":false,"required":["rect","pixel_delta","min_changed_ratio"],"properties":{"rect":{"$ref":"#/$defs/rect"},"pixel_delta":{"type":"integer","minimum":10,"maximum":80},"min_changed_ratio":{"type":"number","minimum":0.01,"maximum":0.5}}}}},"person_detector":{"type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"person_detector"},"settings":{"type":"object","additionalProperties":false,"required":["min_confidence"],"properties":{"min_confidence":{"type":"number","minimum":0.3,"maximum":0.95}}}}},"line_counter":{"type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"line_counter"},"settings":{"type":"object","additionalProperties":false,"required":["line"],"properties":{"line":{"type":"array","minItems":2,"maxItems":2,"items":{"$ref":"#/$defs/point"}}}}}},"looming":{"$comment":"Stretch block. The runner rejects it unless status.capabilities lists looming.","type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"looming"},"settings":{"type":"object","additionalProperties":false,"required":["min_expansion_per_second"],"properties":{"min_expansion_per_second":{"type":"number","minimum":0.1,"maximum":5}}}}},"brain_none":{"type":"object","additionalProperties":false,"required":["type"],"properties":{"type":{"const":"none"}}},"brain_flybrain":{"$comment":"Steering reads only color_finder (and looming when present), never person results.","type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"flybrain"},"settings":{"type":"object","additionalProperties":false,"required":["turn_gain","deadband"],"properties":{"turn_gain":{"type":"number","minimum":0.1,"maximum":2},"deadband":{"type":"number","minimum":0.02,"maximum":0.25}}}}},"alert":{"$comment":"In-app badge with a fixed message. No email, SMS, police or discipline reports.","type":"object","additionalProperties":false,"required":["type","template"],"properties":{"type":{"const":"alert"},"template":{"enum":["motion_detected","count_changed"]}}},"motors":{"$comment":"The runner uses the lower of this and the local tested speed cap. Cannot arm motors.","type":"object","additionalProperties":false,"required":["type","max_speed_ratio"],"properties":{"type":{"const":"motors"},"max_speed_ratio":{"type":"number","minimum":0.05,"maximum":0.25}}},"is_color_finder":{"type":"object","required":["type"],"properties":{"type":{"const":"color_finder"}}},"is_person_detector":{"type":"object","required":["type"],"properties":{"type":{"const":"person_detector"}}},"is_line_counter":{"type":"object","required":["type"],"properties":{"type":{"const":"line_counter"}}},"is_motors":{"type":"object","required":["type"],"properties":{"type":{"const":"motors"}}}}};
const schema32 = {"type":"object","additionalProperties":false,"required":["type"],"properties":{"type":{"const":"none"}}};
const schema37 = {"type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"person_detector"},"settings":{"type":"object","additionalProperties":false,"required":["min_confidence"],"properties":{"min_confidence":{"type":"number","minimum":0.3,"maximum":0.95}}}}};
const schema40 = {"type":"object","required":["type"],"properties":{"type":{"const":"color_finder"}}};
const schema41 = {"type":"object","required":["type"],"properties":{"type":{"const":"motors"}}};
const schema43 = {"type":"object","required":["type"],"properties":{"type":{"const":"line_counter"}}};
const schema44 = {"type":"object","required":["type"],"properties":{"type":{"const":"person_detector"}}};
const schema45 = {"type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"color_finder"},"settings":{"type":"object","additionalProperties":false,"required":["hue_center","hue_half_width","saturation_min","value_min","min_area_ratio"],"properties":{"hue_center":{"type":"integer","minimum":0,"maximum":179},"hue_half_width":{"type":"integer","minimum":1,"maximum":30},"saturation_min":{"type":"integer","minimum":50,"maximum":255},"value_min":{"type":"integer","minimum":30,"maximum":255},"min_area_ratio":{"type":"number","minimum":0.001,"maximum":0.25}}}}};
const schema49 = {"$comment":"Stretch block. The runner rejects it unless status.capabilities lists looming.","type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"looming"},"settings":{"type":"object","additionalProperties":false,"required":["min_expansion_per_second"],"properties":{"min_expansion_per_second":{"type":"number","minimum":0.1,"maximum":5}}}}};
const schema51 = {"$comment":"Steering reads only color_finder (and looming when present), never person results.","type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"flybrain"},"settings":{"type":"object","additionalProperties":false,"required":["turn_gain","deadband"],"properties":{"turn_gain":{"type":"number","minimum":0.1,"maximum":2},"deadband":{"type":"number","minimum":0.02,"maximum":0.25}}}}};
const schema52 = {"$comment":"In-app badge with a fixed message. No email, SMS, police or discipline reports.","type":"object","additionalProperties":false,"required":["type","template"],"properties":{"type":{"const":"alert"},"template":{"enum":["motion_detected","count_changed"]}}};
const schema53 = {"$comment":"The runner uses the lower of this and the local tested speed cap. Cannot arm motors.","type":"object","additionalProperties":false,"required":["type","max_speed_ratio"],"properties":{"type":{"const":"motors"},"max_speed_ratio":{"type":"number","minimum":0.05,"maximum":0.25}}};
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

const schema46 = {"type":"object","additionalProperties":false,"required":["type","settings"],"properties":{"type":{"const":"motion_zone"},"settings":{"type":"object","additionalProperties":false,"required":["rect","pixel_delta","min_changed_ratio"],"properties":{"rect":{"$ref":"#/$defs/rect"},"pixel_delta":{"type":"integer","minimum":10,"maximum":80},"min_changed_ratio":{"type":"number","minimum":0.01,"maximum":0.5}}}}};
const schema47 = {"$comment":"[left, top, right, bottom], normalized 0..1; left < right and top < bottom are checked by the runner.","type":"array","minItems":4,"maxItems":4,"items":{"type":"number","minimum":0,"maximum":1}};

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
let valid28 = true;
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
if(Array.isArray(data21)){
const _errs64 = errors;
const len4 = data21.length;
for(let i4=0; i4<len4; i4++){
let data22 = data21[i4];
const _errs65 = errors;
const _errs66 = errors;
if(errors === _errs66){
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
if("line_counter" !== data22.type){
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
var valid30 = _errs65 === errors;
if(valid30){
break;
}
}
if(!valid30){
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
errors = _errs64;
if(vErrors !== null){
if(_errs64){
vErrors.length = _errs64;
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
var _valid3 = _errs62 === errors;
errors = _errs61;
if(vErrors !== null){
if(_errs61){
vErrors.length = _errs61;
}
else {
vErrors = null;
}
}
if(_valid3){
const _errs69 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.blocks !== undefined){
let data24 = data.blocks;
if(Array.isArray(data24)){
const _errs71 = errors;
const len5 = data24.length;
for(let i5=0; i5<len5; i5++){
let data25 = data24[i5];
const _errs72 = errors;
if(data25 && typeof data25 == "object" && !Array.isArray(data25)){
if(data25.type === undefined){
const err43 = {instancePath:instancePath+"/blocks/" + i5,schemaPath:"#/$defs/is_person_detector/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err43];
}
else {
vErrors.push(err43);
}
errors++;
}
if(data25.type !== undefined){
if("person_detector" !== data25.type){
const err44 = {instancePath:instancePath+"/blocks/" + i5+"/type",schemaPath:"#/$defs/is_person_detector/properties/type/const",keyword:"const",params:{allowedValue: "person_detector"},message:"must be equal to constant"};
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
else {
const err45 = {instancePath:instancePath+"/blocks/" + i5,schemaPath:"#/$defs/is_person_detector/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err45];
}
else {
vErrors.push(err45);
}
errors++;
}
var valid34 = _errs72 === errors;
if(valid34){
break;
}
}
if(!valid34){
const err46 = {instancePath:instancePath+"/blocks",schemaPath:"#/allOf/2/then/properties/blocks/contains",keyword:"contains",params:{minContains: 1},message:"must contain at least 1 valid item(s)"};
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
}
}
var _valid3 = _errs69 === errors;
valid28 = _valid3;
if(valid28){
var props3 = {};
props3.blocks = true;
}
}
if(!valid28){
const err47 = {instancePath,schemaPath:"#/allOf/2/if",keyword:"if",params:{failingKeyword: "then"},message:"must match \"then\" schema"};
if(vErrors === null){
vErrors = [err47];
}
else {
vErrors.push(err47);
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
const err48 = {instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: "version"},message:"must have required property '"+"version"+"'"};
if(vErrors === null){
vErrors = [err48];
}
else {
vErrors.push(err48);
}
errors++;
}
if(data.language === undefined){
const err49 = {instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: "language"},message:"must have required property '"+"language"+"'"};
if(vErrors === null){
vErrors = [err49];
}
else {
vErrors.push(err49);
}
errors++;
}
if(data.camera === undefined){
const err50 = {instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: "camera"},message:"must have required property '"+"camera"+"'"};
if(vErrors === null){
vErrors = [err50];
}
else {
vErrors.push(err50);
}
errors++;
}
if(data.blocks === undefined){
const err51 = {instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: "blocks"},message:"must have required property '"+"blocks"+"'"};
if(vErrors === null){
vErrors = [err51];
}
else {
vErrors.push(err51);
}
errors++;
}
if(data.brain === undefined){
const err52 = {instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: "brain"},message:"must have required property '"+"brain"+"'"};
if(vErrors === null){
vErrors = [err52];
}
else {
vErrors.push(err52);
}
errors++;
}
if(data.actions === undefined){
const err53 = {instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: "actions"},message:"must have required property '"+"actions"+"'"};
if(vErrors === null){
vErrors = [err53];
}
else {
vErrors.push(err53);
}
errors++;
}
if(data.privacy === undefined){
const err54 = {instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: "privacy"},message:"must have required property '"+"privacy"+"'"};
if(vErrors === null){
vErrors = [err54];
}
else {
vErrors.push(err54);
}
errors++;
}
for(const key3 in data){
if(!(((((((key3 === "version") || (key3 === "language")) || (key3 === "camera")) || (key3 === "blocks")) || (key3 === "brain")) || (key3 === "actions")) || (key3 === "privacy"))){
const err55 = {instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key3},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err55];
}
else {
vErrors.push(err55);
}
errors++;
}
}
if(data.version !== undefined){
if(1 !== data.version){
const err56 = {instancePath:instancePath+"/version",schemaPath:"#/properties/version/const",keyword:"const",params:{allowedValue: 1},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err56];
}
else {
vErrors.push(err56);
}
errors++;
}
}
if(data.language !== undefined){
let data28 = data.language;
if(!(((data28 === "uz") || (data28 === "ru")) || (data28 === "en"))){
const err57 = {instancePath:instancePath+"/language",schemaPath:"#/properties/language/enum",keyword:"enum",params:{allowedValues: schema31.properties.language.enum},message:"must be equal to one of the allowed values"};
if(vErrors === null){
vErrors = [err57];
}
else {
vErrors.push(err57);
}
errors++;
}
}
if(data.camera !== undefined){
let data29 = data.camera;
if(data29 && typeof data29 == "object" && !Array.isArray(data29)){
if(data29.source === undefined){
const err58 = {instancePath:instancePath+"/camera",schemaPath:"#/properties/camera/required",keyword:"required",params:{missingProperty: "source"},message:"must have required property '"+"source"+"'"};
if(vErrors === null){
vErrors = [err58];
}
else {
vErrors.push(err58);
}
errors++;
}
if(data29.size === undefined){
const err59 = {instancePath:instancePath+"/camera",schemaPath:"#/properties/camera/required",keyword:"required",params:{missingProperty: "size"},message:"must have required property '"+"size"+"'"};
if(vErrors === null){
vErrors = [err59];
}
else {
vErrors.push(err59);
}
errors++;
}
if(data29.fps === undefined){
const err60 = {instancePath:instancePath+"/camera",schemaPath:"#/properties/camera/required",keyword:"required",params:{missingProperty: "fps"},message:"must have required property '"+"fps"+"'"};
if(vErrors === null){
vErrors = [err60];
}
else {
vErrors.push(err60);
}
errors++;
}
for(const key4 in data29){
if(!(((key4 === "source") || (key4 === "size")) || (key4 === "fps"))){
const err61 = {instancePath:instancePath+"/camera",schemaPath:"#/properties/camera/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key4},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err61];
}
else {
vErrors.push(err61);
}
errors++;
}
}
if(data29.source !== undefined){
if("device_camera" !== data29.source){
const err62 = {instancePath:instancePath+"/camera/source",schemaPath:"#/properties/camera/properties/source/const",keyword:"const",params:{allowedValue: "device_camera"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err62];
}
else {
vErrors.push(err62);
}
errors++;
}
}
if(data29.size !== undefined){
let data31 = data29.size;
if(!((data31 === "320x240") || (data31 === "640x480"))){
const err63 = {instancePath:instancePath+"/camera/size",schemaPath:"#/properties/camera/properties/size/enum",keyword:"enum",params:{allowedValues: schema31.properties.camera.properties.size.enum},message:"must be equal to one of the allowed values"};
if(vErrors === null){
vErrors = [err63];
}
else {
vErrors.push(err63);
}
errors++;
}
}
if(data29.fps !== undefined){
let data32 = data29.fps;
if(!((typeof data32 == "number") && (!(data32 % 1) && !isNaN(data32)))){
const err64 = {instancePath:instancePath+"/camera/fps",schemaPath:"#/properties/camera/properties/fps/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err64];
}
else {
vErrors.push(err64);
}
errors++;
}
if(typeof data32 == "number"){
if(data32 > 15 || isNaN(data32)){
const err65 = {instancePath:instancePath+"/camera/fps",schemaPath:"#/properties/camera/properties/fps/maximum",keyword:"maximum",params:{comparison: "<=", limit: 15},message:"must be <= 15"};
if(vErrors === null){
vErrors = [err65];
}
else {
vErrors.push(err65);
}
errors++;
}
if(data32 < 1 || isNaN(data32)){
const err66 = {instancePath:instancePath+"/camera/fps",schemaPath:"#/properties/camera/properties/fps/minimum",keyword:"minimum",params:{comparison: ">=", limit: 1},message:"must be >= 1"};
if(vErrors === null){
vErrors = [err66];
}
else {
vErrors.push(err66);
}
errors++;
}
}
}
}
else {
const err67 = {instancePath:instancePath+"/camera",schemaPath:"#/properties/camera/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err67];
}
else {
vErrors.push(err67);
}
errors++;
}
}
if(data.blocks !== undefined){
let data33 = data.blocks;
if(Array.isArray(data33)){
if(data33.length > 7){
const err68 = {instancePath:instancePath+"/blocks",schemaPath:"#/properties/blocks/maxItems",keyword:"maxItems",params:{limit: 7},message:"must NOT have more than 7 items"};
if(vErrors === null){
vErrors = [err68];
}
else {
vErrors.push(err68);
}
errors++;
}
if(data33.length < 2){
const err69 = {instancePath:instancePath+"/blocks",schemaPath:"#/properties/blocks/minItems",keyword:"minItems",params:{limit: 2},message:"must NOT have fewer than 2 items"};
if(vErrors === null){
vErrors = [err69];
}
else {
vErrors.push(err69);
}
errors++;
}
const len6 = data33.length;
if(len6 > 0){
if(!(validate21(data33[0], {instancePath:instancePath+"/blocks/0",parentData:data33,parentDataProperty:0,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate21.errors : vErrors.concat(validate21.errors);
errors = vErrors.length;
}
}
if(len6 > 1){
if(!(validate23(data33[1], {instancePath:instancePath+"/blocks/1",parentData:data33,parentDataProperty:1,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate23.errors : vErrors.concat(validate23.errors);
errors = vErrors.length;
}
}
const len7 = data33.length;
var valid40 = len7 <= 2;
if(!valid40){
for(let i6=2; i6<len7; i6++){
let data36 = data33[i6];
const _errs90 = errors;
const _errs91 = errors;
let valid41 = false;
let passing1 = null;
const _errs92 = errors;
if(data36 && typeof data36 == "object" && !Array.isArray(data36)){
if(data36.type === undefined){
const err70 = {instancePath:instancePath+"/blocks/" + i6,schemaPath:"#/$defs/color_finder/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err70];
}
else {
vErrors.push(err70);
}
errors++;
}
if(data36.settings === undefined){
const err71 = {instancePath:instancePath+"/blocks/" + i6,schemaPath:"#/$defs/color_finder/required",keyword:"required",params:{missingProperty: "settings"},message:"must have required property '"+"settings"+"'"};
if(vErrors === null){
vErrors = [err71];
}
else {
vErrors.push(err71);
}
errors++;
}
for(const key5 in data36){
if(!((key5 === "type") || (key5 === "settings"))){
const err72 = {instancePath:instancePath+"/blocks/" + i6,schemaPath:"#/$defs/color_finder/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key5},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err72];
}
else {
vErrors.push(err72);
}
errors++;
}
}
if(data36.type !== undefined){
if("color_finder" !== data36.type){
const err73 = {instancePath:instancePath+"/blocks/" + i6+"/type",schemaPath:"#/$defs/color_finder/properties/type/const",keyword:"const",params:{allowedValue: "color_finder"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err73];
}
else {
vErrors.push(err73);
}
errors++;
}
}
if(data36.settings !== undefined){
let data38 = data36.settings;
if(data38 && typeof data38 == "object" && !Array.isArray(data38)){
if(data38.hue_center === undefined){
const err74 = {instancePath:instancePath+"/blocks/" + i6+"/settings",schemaPath:"#/$defs/color_finder/properties/settings/required",keyword:"required",params:{missingProperty: "hue_center"},message:"must have required property '"+"hue_center"+"'"};
if(vErrors === null){
vErrors = [err74];
}
else {
vErrors.push(err74);
}
errors++;
}
if(data38.hue_half_width === undefined){
const err75 = {instancePath:instancePath+"/blocks/" + i6+"/settings",schemaPath:"#/$defs/color_finder/properties/settings/required",keyword:"required",params:{missingProperty: "hue_half_width"},message:"must have required property '"+"hue_half_width"+"'"};
if(vErrors === null){
vErrors = [err75];
}
else {
vErrors.push(err75);
}
errors++;
}
if(data38.saturation_min === undefined){
const err76 = {instancePath:instancePath+"/blocks/" + i6+"/settings",schemaPath:"#/$defs/color_finder/properties/settings/required",keyword:"required",params:{missingProperty: "saturation_min"},message:"must have required property '"+"saturation_min"+"'"};
if(vErrors === null){
vErrors = [err76];
}
else {
vErrors.push(err76);
}
errors++;
}
if(data38.value_min === undefined){
const err77 = {instancePath:instancePath+"/blocks/" + i6+"/settings",schemaPath:"#/$defs/color_finder/properties/settings/required",keyword:"required",params:{missingProperty: "value_min"},message:"must have required property '"+"value_min"+"'"};
if(vErrors === null){
vErrors = [err77];
}
else {
vErrors.push(err77);
}
errors++;
}
if(data38.min_area_ratio === undefined){
const err78 = {instancePath:instancePath+"/blocks/" + i6+"/settings",schemaPath:"#/$defs/color_finder/properties/settings/required",keyword:"required",params:{missingProperty: "min_area_ratio"},message:"must have required property '"+"min_area_ratio"+"'"};
if(vErrors === null){
vErrors = [err78];
}
else {
vErrors.push(err78);
}
errors++;
}
for(const key6 in data38){
if(!(((((key6 === "hue_center") || (key6 === "hue_half_width")) || (key6 === "saturation_min")) || (key6 === "value_min")) || (key6 === "min_area_ratio"))){
const err79 = {instancePath:instancePath+"/blocks/" + i6+"/settings",schemaPath:"#/$defs/color_finder/properties/settings/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key6},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err79];
}
else {
vErrors.push(err79);
}
errors++;
}
}
if(data38.hue_center !== undefined){
let data39 = data38.hue_center;
if(!((typeof data39 == "number") && (!(data39 % 1) && !isNaN(data39)))){
const err80 = {instancePath:instancePath+"/blocks/" + i6+"/settings/hue_center",schemaPath:"#/$defs/color_finder/properties/settings/properties/hue_center/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err80];
}
else {
vErrors.push(err80);
}
errors++;
}
if(typeof data39 == "number"){
if(data39 > 179 || isNaN(data39)){
const err81 = {instancePath:instancePath+"/blocks/" + i6+"/settings/hue_center",schemaPath:"#/$defs/color_finder/properties/settings/properties/hue_center/maximum",keyword:"maximum",params:{comparison: "<=", limit: 179},message:"must be <= 179"};
if(vErrors === null){
vErrors = [err81];
}
else {
vErrors.push(err81);
}
errors++;
}
if(data39 < 0 || isNaN(data39)){
const err82 = {instancePath:instancePath+"/blocks/" + i6+"/settings/hue_center",schemaPath:"#/$defs/color_finder/properties/settings/properties/hue_center/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err82];
}
else {
vErrors.push(err82);
}
errors++;
}
}
}
if(data38.hue_half_width !== undefined){
let data40 = data38.hue_half_width;
if(!((typeof data40 == "number") && (!(data40 % 1) && !isNaN(data40)))){
const err83 = {instancePath:instancePath+"/blocks/" + i6+"/settings/hue_half_width",schemaPath:"#/$defs/color_finder/properties/settings/properties/hue_half_width/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err83];
}
else {
vErrors.push(err83);
}
errors++;
}
if(typeof data40 == "number"){
if(data40 > 30 || isNaN(data40)){
const err84 = {instancePath:instancePath+"/blocks/" + i6+"/settings/hue_half_width",schemaPath:"#/$defs/color_finder/properties/settings/properties/hue_half_width/maximum",keyword:"maximum",params:{comparison: "<=", limit: 30},message:"must be <= 30"};
if(vErrors === null){
vErrors = [err84];
}
else {
vErrors.push(err84);
}
errors++;
}
if(data40 < 1 || isNaN(data40)){
const err85 = {instancePath:instancePath+"/blocks/" + i6+"/settings/hue_half_width",schemaPath:"#/$defs/color_finder/properties/settings/properties/hue_half_width/minimum",keyword:"minimum",params:{comparison: ">=", limit: 1},message:"must be >= 1"};
if(vErrors === null){
vErrors = [err85];
}
else {
vErrors.push(err85);
}
errors++;
}
}
}
if(data38.saturation_min !== undefined){
let data41 = data38.saturation_min;
if(!((typeof data41 == "number") && (!(data41 % 1) && !isNaN(data41)))){
const err86 = {instancePath:instancePath+"/blocks/" + i6+"/settings/saturation_min",schemaPath:"#/$defs/color_finder/properties/settings/properties/saturation_min/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err86];
}
else {
vErrors.push(err86);
}
errors++;
}
if(typeof data41 == "number"){
if(data41 > 255 || isNaN(data41)){
const err87 = {instancePath:instancePath+"/blocks/" + i6+"/settings/saturation_min",schemaPath:"#/$defs/color_finder/properties/settings/properties/saturation_min/maximum",keyword:"maximum",params:{comparison: "<=", limit: 255},message:"must be <= 255"};
if(vErrors === null){
vErrors = [err87];
}
else {
vErrors.push(err87);
}
errors++;
}
if(data41 < 50 || isNaN(data41)){
const err88 = {instancePath:instancePath+"/blocks/" + i6+"/settings/saturation_min",schemaPath:"#/$defs/color_finder/properties/settings/properties/saturation_min/minimum",keyword:"minimum",params:{comparison: ">=", limit: 50},message:"must be >= 50"};
if(vErrors === null){
vErrors = [err88];
}
else {
vErrors.push(err88);
}
errors++;
}
}
}
if(data38.value_min !== undefined){
let data42 = data38.value_min;
if(!((typeof data42 == "number") && (!(data42 % 1) && !isNaN(data42)))){
const err89 = {instancePath:instancePath+"/blocks/" + i6+"/settings/value_min",schemaPath:"#/$defs/color_finder/properties/settings/properties/value_min/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err89];
}
else {
vErrors.push(err89);
}
errors++;
}
if(typeof data42 == "number"){
if(data42 > 255 || isNaN(data42)){
const err90 = {instancePath:instancePath+"/blocks/" + i6+"/settings/value_min",schemaPath:"#/$defs/color_finder/properties/settings/properties/value_min/maximum",keyword:"maximum",params:{comparison: "<=", limit: 255},message:"must be <= 255"};
if(vErrors === null){
vErrors = [err90];
}
else {
vErrors.push(err90);
}
errors++;
}
if(data42 < 30 || isNaN(data42)){
const err91 = {instancePath:instancePath+"/blocks/" + i6+"/settings/value_min",schemaPath:"#/$defs/color_finder/properties/settings/properties/value_min/minimum",keyword:"minimum",params:{comparison: ">=", limit: 30},message:"must be >= 30"};
if(vErrors === null){
vErrors = [err91];
}
else {
vErrors.push(err91);
}
errors++;
}
}
}
if(data38.min_area_ratio !== undefined){
let data43 = data38.min_area_ratio;
if(typeof data43 == "number"){
if(data43 > 0.25 || isNaN(data43)){
const err92 = {instancePath:instancePath+"/blocks/" + i6+"/settings/min_area_ratio",schemaPath:"#/$defs/color_finder/properties/settings/properties/min_area_ratio/maximum",keyword:"maximum",params:{comparison: "<=", limit: 0.25},message:"must be <= 0.25"};
if(vErrors === null){
vErrors = [err92];
}
else {
vErrors.push(err92);
}
errors++;
}
if(data43 < 0.001 || isNaN(data43)){
const err93 = {instancePath:instancePath+"/blocks/" + i6+"/settings/min_area_ratio",schemaPath:"#/$defs/color_finder/properties/settings/properties/min_area_ratio/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0.001},message:"must be >= 0.001"};
if(vErrors === null){
vErrors = [err93];
}
else {
vErrors.push(err93);
}
errors++;
}
}
else {
const err94 = {instancePath:instancePath+"/blocks/" + i6+"/settings/min_area_ratio",schemaPath:"#/$defs/color_finder/properties/settings/properties/min_area_ratio/type",keyword:"type",params:{type: "number"},message:"must be number"};
if(vErrors === null){
vErrors = [err94];
}
else {
vErrors.push(err94);
}
errors++;
}
}
}
else {
const err95 = {instancePath:instancePath+"/blocks/" + i6+"/settings",schemaPath:"#/$defs/color_finder/properties/settings/type",keyword:"type",params:{type: "object"},message:"must be object"};
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
else {
const err96 = {instancePath:instancePath+"/blocks/" + i6,schemaPath:"#/$defs/color_finder/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err96];
}
else {
vErrors.push(err96);
}
errors++;
}
var _valid4 = _errs92 === errors;
if(_valid4){
valid41 = true;
passing1 = 0;
var props4 = true;
}
const _errs110 = errors;
if(!(validate29(data36, {instancePath:instancePath+"/blocks/" + i6,parentData:data33,parentDataProperty:i6,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate29.errors : vErrors.concat(validate29.errors);
errors = vErrors.length;
}
var _valid4 = _errs110 === errors;
if(_valid4 && valid41){
valid41 = false;
passing1 = [passing1, 1];
}
else {
if(_valid4){
valid41 = true;
passing1 = 1;
if(props4 !== true){
props4 = true;
}
}
const _errs111 = errors;
if(data36 && typeof data36 == "object" && !Array.isArray(data36)){
if(data36.type === undefined){
const err97 = {instancePath:instancePath+"/blocks/" + i6,schemaPath:"#/$defs/person_detector/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err97];
}
else {
vErrors.push(err97);
}
errors++;
}
if(data36.settings === undefined){
const err98 = {instancePath:instancePath+"/blocks/" + i6,schemaPath:"#/$defs/person_detector/required",keyword:"required",params:{missingProperty: "settings"},message:"must have required property '"+"settings"+"'"};
if(vErrors === null){
vErrors = [err98];
}
else {
vErrors.push(err98);
}
errors++;
}
for(const key7 in data36){
if(!((key7 === "type") || (key7 === "settings"))){
const err99 = {instancePath:instancePath+"/blocks/" + i6,schemaPath:"#/$defs/person_detector/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key7},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err99];
}
else {
vErrors.push(err99);
}
errors++;
}
}
if(data36.type !== undefined){
if("person_detector" !== data36.type){
const err100 = {instancePath:instancePath+"/blocks/" + i6+"/type",schemaPath:"#/$defs/person_detector/properties/type/const",keyword:"const",params:{allowedValue: "person_detector"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err100];
}
else {
vErrors.push(err100);
}
errors++;
}
}
if(data36.settings !== undefined){
let data45 = data36.settings;
if(data45 && typeof data45 == "object" && !Array.isArray(data45)){
if(data45.min_confidence === undefined){
const err101 = {instancePath:instancePath+"/blocks/" + i6+"/settings",schemaPath:"#/$defs/person_detector/properties/settings/required",keyword:"required",params:{missingProperty: "min_confidence"},message:"must have required property '"+"min_confidence"+"'"};
if(vErrors === null){
vErrors = [err101];
}
else {
vErrors.push(err101);
}
errors++;
}
for(const key8 in data45){
if(!(key8 === "min_confidence")){
const err102 = {instancePath:instancePath+"/blocks/" + i6+"/settings",schemaPath:"#/$defs/person_detector/properties/settings/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key8},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err102];
}
else {
vErrors.push(err102);
}
errors++;
}
}
if(data45.min_confidence !== undefined){
let data46 = data45.min_confidence;
if(typeof data46 == "number"){
if(data46 > 0.95 || isNaN(data46)){
const err103 = {instancePath:instancePath+"/blocks/" + i6+"/settings/min_confidence",schemaPath:"#/$defs/person_detector/properties/settings/properties/min_confidence/maximum",keyword:"maximum",params:{comparison: "<=", limit: 0.95},message:"must be <= 0.95"};
if(vErrors === null){
vErrors = [err103];
}
else {
vErrors.push(err103);
}
errors++;
}
if(data46 < 0.3 || isNaN(data46)){
const err104 = {instancePath:instancePath+"/blocks/" + i6+"/settings/min_confidence",schemaPath:"#/$defs/person_detector/properties/settings/properties/min_confidence/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0.3},message:"must be >= 0.3"};
if(vErrors === null){
vErrors = [err104];
}
else {
vErrors.push(err104);
}
errors++;
}
}
else {
const err105 = {instancePath:instancePath+"/blocks/" + i6+"/settings/min_confidence",schemaPath:"#/$defs/person_detector/properties/settings/properties/min_confidence/type",keyword:"type",params:{type: "number"},message:"must be number"};
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
const err106 = {instancePath:instancePath+"/blocks/" + i6+"/settings",schemaPath:"#/$defs/person_detector/properties/settings/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err106];
}
else {
vErrors.push(err106);
}
errors++;
}
}
}
else {
const err107 = {instancePath:instancePath+"/blocks/" + i6,schemaPath:"#/$defs/person_detector/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err107];
}
else {
vErrors.push(err107);
}
errors++;
}
var _valid4 = _errs111 === errors;
if(_valid4 && valid41){
valid41 = false;
passing1 = [passing1, 2];
}
else {
if(_valid4){
valid41 = true;
passing1 = 2;
if(props4 !== true){
props4 = true;
}
}
const _errs121 = errors;
if(!(validate25(data36, {instancePath:instancePath+"/blocks/" + i6,parentData:data33,parentDataProperty:i6,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate25.errors : vErrors.concat(validate25.errors);
errors = vErrors.length;
}
var _valid4 = _errs121 === errors;
if(_valid4 && valid41){
valid41 = false;
passing1 = [passing1, 3];
}
else {
if(_valid4){
valid41 = true;
passing1 = 3;
if(props4 !== true){
props4 = true;
}
}
const _errs122 = errors;
if(data36 && typeof data36 == "object" && !Array.isArray(data36)){
if(data36.type === undefined){
const err108 = {instancePath:instancePath+"/blocks/" + i6,schemaPath:"#/$defs/looming/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err108];
}
else {
vErrors.push(err108);
}
errors++;
}
if(data36.settings === undefined){
const err109 = {instancePath:instancePath+"/blocks/" + i6,schemaPath:"#/$defs/looming/required",keyword:"required",params:{missingProperty: "settings"},message:"must have required property '"+"settings"+"'"};
if(vErrors === null){
vErrors = [err109];
}
else {
vErrors.push(err109);
}
errors++;
}
for(const key9 in data36){
if(!((key9 === "type") || (key9 === "settings"))){
const err110 = {instancePath:instancePath+"/blocks/" + i6,schemaPath:"#/$defs/looming/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key9},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err110];
}
else {
vErrors.push(err110);
}
errors++;
}
}
if(data36.type !== undefined){
if("looming" !== data36.type){
const err111 = {instancePath:instancePath+"/blocks/" + i6+"/type",schemaPath:"#/$defs/looming/properties/type/const",keyword:"const",params:{allowedValue: "looming"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err111];
}
else {
vErrors.push(err111);
}
errors++;
}
}
if(data36.settings !== undefined){
let data48 = data36.settings;
if(data48 && typeof data48 == "object" && !Array.isArray(data48)){
if(data48.min_expansion_per_second === undefined){
const err112 = {instancePath:instancePath+"/blocks/" + i6+"/settings",schemaPath:"#/$defs/looming/properties/settings/required",keyword:"required",params:{missingProperty: "min_expansion_per_second"},message:"must have required property '"+"min_expansion_per_second"+"'"};
if(vErrors === null){
vErrors = [err112];
}
else {
vErrors.push(err112);
}
errors++;
}
for(const key10 in data48){
if(!(key10 === "min_expansion_per_second")){
const err113 = {instancePath:instancePath+"/blocks/" + i6+"/settings",schemaPath:"#/$defs/looming/properties/settings/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key10},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err113];
}
else {
vErrors.push(err113);
}
errors++;
}
}
if(data48.min_expansion_per_second !== undefined){
let data49 = data48.min_expansion_per_second;
if(typeof data49 == "number"){
if(data49 > 5 || isNaN(data49)){
const err114 = {instancePath:instancePath+"/blocks/" + i6+"/settings/min_expansion_per_second",schemaPath:"#/$defs/looming/properties/settings/properties/min_expansion_per_second/maximum",keyword:"maximum",params:{comparison: "<=", limit: 5},message:"must be <= 5"};
if(vErrors === null){
vErrors = [err114];
}
else {
vErrors.push(err114);
}
errors++;
}
if(data49 < 0.1 || isNaN(data49)){
const err115 = {instancePath:instancePath+"/blocks/" + i6+"/settings/min_expansion_per_second",schemaPath:"#/$defs/looming/properties/settings/properties/min_expansion_per_second/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0.1},message:"must be >= 0.1"};
if(vErrors === null){
vErrors = [err115];
}
else {
vErrors.push(err115);
}
errors++;
}
}
else {
const err116 = {instancePath:instancePath+"/blocks/" + i6+"/settings/min_expansion_per_second",schemaPath:"#/$defs/looming/properties/settings/properties/min_expansion_per_second/type",keyword:"type",params:{type: "number"},message:"must be number"};
if(vErrors === null){
vErrors = [err116];
}
else {
vErrors.push(err116);
}
errors++;
}
}
}
else {
const err117 = {instancePath:instancePath+"/blocks/" + i6+"/settings",schemaPath:"#/$defs/looming/properties/settings/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err117];
}
else {
vErrors.push(err117);
}
errors++;
}
}
}
else {
const err118 = {instancePath:instancePath+"/blocks/" + i6,schemaPath:"#/$defs/looming/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err118];
}
else {
vErrors.push(err118);
}
errors++;
}
var _valid4 = _errs122 === errors;
if(_valid4 && valid41){
valid41 = false;
passing1 = [passing1, 4];
}
else {
if(_valid4){
valid41 = true;
passing1 = 4;
if(props4 !== true){
props4 = true;
}
}
}
}
}
}
if(!valid41){
const err119 = {instancePath:instancePath+"/blocks/" + i6,schemaPath:"#/properties/blocks/items/oneOf",keyword:"oneOf",params:{passingSchemas: passing1},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err119];
}
else {
vErrors.push(err119);
}
errors++;
}
else {
errors = _errs91;
if(vErrors !== null){
if(_errs91){
vErrors.length = _errs91;
}
else {
vErrors = null;
}
}
}
var valid40 = _errs90 === errors;
}
}
}
else {
const err120 = {instancePath:instancePath+"/blocks",schemaPath:"#/properties/blocks/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err120];
}
else {
vErrors.push(err120);
}
errors++;
}
}
if(data.brain !== undefined){
let data50 = data.brain;
const _errs134 = errors;
let valid51 = false;
let passing2 = null;
const _errs135 = errors;
if(data50 && typeof data50 == "object" && !Array.isArray(data50)){
if(data50.type === undefined){
const err121 = {instancePath:instancePath+"/brain",schemaPath:"#/$defs/brain_none/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err121];
}
else {
vErrors.push(err121);
}
errors++;
}
for(const key11 in data50){
if(!(key11 === "type")){
const err122 = {instancePath:instancePath+"/brain",schemaPath:"#/$defs/brain_none/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key11},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err122];
}
else {
vErrors.push(err122);
}
errors++;
}
}
if(data50.type !== undefined){
if("none" !== data50.type){
const err123 = {instancePath:instancePath+"/brain/type",schemaPath:"#/$defs/brain_none/properties/type/const",keyword:"const",params:{allowedValue: "none"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err123];
}
else {
vErrors.push(err123);
}
errors++;
}
}
}
else {
const err124 = {instancePath:instancePath+"/brain",schemaPath:"#/$defs/brain_none/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err124];
}
else {
vErrors.push(err124);
}
errors++;
}
var _valid5 = _errs135 === errors;
if(_valid5){
valid51 = true;
passing2 = 0;
var props5 = true;
}
const _errs140 = errors;
if(data50 && typeof data50 == "object" && !Array.isArray(data50)){
if(data50.type === undefined){
const err125 = {instancePath:instancePath+"/brain",schemaPath:"#/$defs/brain_flybrain/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err125];
}
else {
vErrors.push(err125);
}
errors++;
}
if(data50.settings === undefined){
const err126 = {instancePath:instancePath+"/brain",schemaPath:"#/$defs/brain_flybrain/required",keyword:"required",params:{missingProperty: "settings"},message:"must have required property '"+"settings"+"'"};
if(vErrors === null){
vErrors = [err126];
}
else {
vErrors.push(err126);
}
errors++;
}
for(const key12 in data50){
if(!((key12 === "type") || (key12 === "settings"))){
const err127 = {instancePath:instancePath+"/brain",schemaPath:"#/$defs/brain_flybrain/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key12},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err127];
}
else {
vErrors.push(err127);
}
errors++;
}
}
if(data50.type !== undefined){
if("flybrain" !== data50.type){
const err128 = {instancePath:instancePath+"/brain/type",schemaPath:"#/$defs/brain_flybrain/properties/type/const",keyword:"const",params:{allowedValue: "flybrain"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err128];
}
else {
vErrors.push(err128);
}
errors++;
}
}
if(data50.settings !== undefined){
let data53 = data50.settings;
if(data53 && typeof data53 == "object" && !Array.isArray(data53)){
if(data53.turn_gain === undefined){
const err129 = {instancePath:instancePath+"/brain/settings",schemaPath:"#/$defs/brain_flybrain/properties/settings/required",keyword:"required",params:{missingProperty: "turn_gain"},message:"must have required property '"+"turn_gain"+"'"};
if(vErrors === null){
vErrors = [err129];
}
else {
vErrors.push(err129);
}
errors++;
}
if(data53.deadband === undefined){
const err130 = {instancePath:instancePath+"/brain/settings",schemaPath:"#/$defs/brain_flybrain/properties/settings/required",keyword:"required",params:{missingProperty: "deadband"},message:"must have required property '"+"deadband"+"'"};
if(vErrors === null){
vErrors = [err130];
}
else {
vErrors.push(err130);
}
errors++;
}
for(const key13 in data53){
if(!((key13 === "turn_gain") || (key13 === "deadband"))){
const err131 = {instancePath:instancePath+"/brain/settings",schemaPath:"#/$defs/brain_flybrain/properties/settings/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key13},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err131];
}
else {
vErrors.push(err131);
}
errors++;
}
}
if(data53.turn_gain !== undefined){
let data54 = data53.turn_gain;
if(typeof data54 == "number"){
if(data54 > 2 || isNaN(data54)){
const err132 = {instancePath:instancePath+"/brain/settings/turn_gain",schemaPath:"#/$defs/brain_flybrain/properties/settings/properties/turn_gain/maximum",keyword:"maximum",params:{comparison: "<=", limit: 2},message:"must be <= 2"};
if(vErrors === null){
vErrors = [err132];
}
else {
vErrors.push(err132);
}
errors++;
}
if(data54 < 0.1 || isNaN(data54)){
const err133 = {instancePath:instancePath+"/brain/settings/turn_gain",schemaPath:"#/$defs/brain_flybrain/properties/settings/properties/turn_gain/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0.1},message:"must be >= 0.1"};
if(vErrors === null){
vErrors = [err133];
}
else {
vErrors.push(err133);
}
errors++;
}
}
else {
const err134 = {instancePath:instancePath+"/brain/settings/turn_gain",schemaPath:"#/$defs/brain_flybrain/properties/settings/properties/turn_gain/type",keyword:"type",params:{type: "number"},message:"must be number"};
if(vErrors === null){
vErrors = [err134];
}
else {
vErrors.push(err134);
}
errors++;
}
}
if(data53.deadband !== undefined){
let data55 = data53.deadband;
if(typeof data55 == "number"){
if(data55 > 0.25 || isNaN(data55)){
const err135 = {instancePath:instancePath+"/brain/settings/deadband",schemaPath:"#/$defs/brain_flybrain/properties/settings/properties/deadband/maximum",keyword:"maximum",params:{comparison: "<=", limit: 0.25},message:"must be <= 0.25"};
if(vErrors === null){
vErrors = [err135];
}
else {
vErrors.push(err135);
}
errors++;
}
if(data55 < 0.02 || isNaN(data55)){
const err136 = {instancePath:instancePath+"/brain/settings/deadband",schemaPath:"#/$defs/brain_flybrain/properties/settings/properties/deadband/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0.02},message:"must be >= 0.02"};
if(vErrors === null){
vErrors = [err136];
}
else {
vErrors.push(err136);
}
errors++;
}
}
else {
const err137 = {instancePath:instancePath+"/brain/settings/deadband",schemaPath:"#/$defs/brain_flybrain/properties/settings/properties/deadband/type",keyword:"type",params:{type: "number"},message:"must be number"};
if(vErrors === null){
vErrors = [err137];
}
else {
vErrors.push(err137);
}
errors++;
}
}
}
else {
const err138 = {instancePath:instancePath+"/brain/settings",schemaPath:"#/$defs/brain_flybrain/properties/settings/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err138];
}
else {
vErrors.push(err138);
}
errors++;
}
}
}
else {
const err139 = {instancePath:instancePath+"/brain",schemaPath:"#/$defs/brain_flybrain/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err139];
}
else {
vErrors.push(err139);
}
errors++;
}
var _valid5 = _errs140 === errors;
if(_valid5 && valid51){
valid51 = false;
passing2 = [passing2, 1];
}
else {
if(_valid5){
valid51 = true;
passing2 = 1;
if(props5 !== true){
props5 = true;
}
}
}
if(!valid51){
const err140 = {instancePath:instancePath+"/brain",schemaPath:"#/properties/brain/oneOf",keyword:"oneOf",params:{passingSchemas: passing2},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err140];
}
else {
vErrors.push(err140);
}
errors++;
}
else {
errors = _errs134;
if(vErrors !== null){
if(_errs134){
vErrors.length = _errs134;
}
else {
vErrors = null;
}
}
}
}
if(data.actions !== undefined){
let data56 = data.actions;
if(Array.isArray(data56)){
if(data56.length > 2){
const err141 = {instancePath:instancePath+"/actions",schemaPath:"#/properties/actions/maxItems",keyword:"maxItems",params:{limit: 2},message:"must NOT have more than 2 items"};
if(vErrors === null){
vErrors = [err141];
}
else {
vErrors.push(err141);
}
errors++;
}
if(data56.length < 1){
const err142 = {instancePath:instancePath+"/actions",schemaPath:"#/properties/actions/minItems",keyword:"minItems",params:{limit: 1},message:"must NOT have fewer than 1 items"};
if(vErrors === null){
vErrors = [err142];
}
else {
vErrors.push(err142);
}
errors++;
}
const len8 = data56.length;
if(len8 > 0){
let data57 = data56[0];
if(data57 && typeof data57 == "object" && !Array.isArray(data57)){
if(data57.type === undefined){
const err143 = {instancePath:instancePath+"/actions/0",schemaPath:"#/properties/actions/prefixItems/0/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err143];
}
else {
vErrors.push(err143);
}
errors++;
}
for(const key14 in data57){
if(!(key14 === "type")){
const err144 = {instancePath:instancePath+"/actions/0",schemaPath:"#/properties/actions/prefixItems/0/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key14},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err144];
}
else {
vErrors.push(err144);
}
errors++;
}
}
if(data57.type !== undefined){
if("dashboard" !== data57.type){
const err145 = {instancePath:instancePath+"/actions/0/type",schemaPath:"#/properties/actions/prefixItems/0/properties/type/const",keyword:"const",params:{allowedValue: "dashboard"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err145];
}
else {
vErrors.push(err145);
}
errors++;
}
}
}
else {
const err146 = {instancePath:instancePath+"/actions/0",schemaPath:"#/properties/actions/prefixItems/0/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err146];
}
else {
vErrors.push(err146);
}
errors++;
}
}
const len9 = data56.length;
var valid59 = len9 <= 1;
if(!valid59){
for(let i7=1; i7<len9; i7++){
let data59 = data56[i7];
const _errs159 = errors;
const _errs160 = errors;
let valid60 = false;
let passing3 = null;
const _errs161 = errors;
if(data59 && typeof data59 == "object" && !Array.isArray(data59)){
if(data59.type === undefined){
const err147 = {instancePath:instancePath+"/actions/" + i7,schemaPath:"#/$defs/alert/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err147];
}
else {
vErrors.push(err147);
}
errors++;
}
if(data59.template === undefined){
const err148 = {instancePath:instancePath+"/actions/" + i7,schemaPath:"#/$defs/alert/required",keyword:"required",params:{missingProperty: "template"},message:"must have required property '"+"template"+"'"};
if(vErrors === null){
vErrors = [err148];
}
else {
vErrors.push(err148);
}
errors++;
}
for(const key15 in data59){
if(!((key15 === "type") || (key15 === "template"))){
const err149 = {instancePath:instancePath+"/actions/" + i7,schemaPath:"#/$defs/alert/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key15},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err149];
}
else {
vErrors.push(err149);
}
errors++;
}
}
if(data59.type !== undefined){
if("alert" !== data59.type){
const err150 = {instancePath:instancePath+"/actions/" + i7+"/type",schemaPath:"#/$defs/alert/properties/type/const",keyword:"const",params:{allowedValue: "alert"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err150];
}
else {
vErrors.push(err150);
}
errors++;
}
}
if(data59.template !== undefined){
let data61 = data59.template;
if(!((data61 === "motion_detected") || (data61 === "count_changed"))){
const err151 = {instancePath:instancePath+"/actions/" + i7+"/template",schemaPath:"#/$defs/alert/properties/template/enum",keyword:"enum",params:{allowedValues: schema52.properties.template.enum},message:"must be equal to one of the allowed values"};
if(vErrors === null){
vErrors = [err151];
}
else {
vErrors.push(err151);
}
errors++;
}
}
}
else {
const err152 = {instancePath:instancePath+"/actions/" + i7,schemaPath:"#/$defs/alert/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err152];
}
else {
vErrors.push(err152);
}
errors++;
}
var _valid6 = _errs161 === errors;
if(_valid6){
valid60 = true;
passing3 = 0;
var props6 = true;
}
const _errs168 = errors;
if(data59 && typeof data59 == "object" && !Array.isArray(data59)){
if(data59.type === undefined){
const err153 = {instancePath:instancePath+"/actions/" + i7,schemaPath:"#/$defs/motors/required",keyword:"required",params:{missingProperty: "type"},message:"must have required property '"+"type"+"'"};
if(vErrors === null){
vErrors = [err153];
}
else {
vErrors.push(err153);
}
errors++;
}
if(data59.max_speed_ratio === undefined){
const err154 = {instancePath:instancePath+"/actions/" + i7,schemaPath:"#/$defs/motors/required",keyword:"required",params:{missingProperty: "max_speed_ratio"},message:"must have required property '"+"max_speed_ratio"+"'"};
if(vErrors === null){
vErrors = [err154];
}
else {
vErrors.push(err154);
}
errors++;
}
for(const key16 in data59){
if(!((key16 === "type") || (key16 === "max_speed_ratio"))){
const err155 = {instancePath:instancePath+"/actions/" + i7,schemaPath:"#/$defs/motors/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key16},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err155];
}
else {
vErrors.push(err155);
}
errors++;
}
}
if(data59.type !== undefined){
if("motors" !== data59.type){
const err156 = {instancePath:instancePath+"/actions/" + i7+"/type",schemaPath:"#/$defs/motors/properties/type/const",keyword:"const",params:{allowedValue: "motors"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err156];
}
else {
vErrors.push(err156);
}
errors++;
}
}
if(data59.max_speed_ratio !== undefined){
let data63 = data59.max_speed_ratio;
if(typeof data63 == "number"){
if(data63 > 0.25 || isNaN(data63)){
const err157 = {instancePath:instancePath+"/actions/" + i7+"/max_speed_ratio",schemaPath:"#/$defs/motors/properties/max_speed_ratio/maximum",keyword:"maximum",params:{comparison: "<=", limit: 0.25},message:"must be <= 0.25"};
if(vErrors === null){
vErrors = [err157];
}
else {
vErrors.push(err157);
}
errors++;
}
if(data63 < 0.05 || isNaN(data63)){
const err158 = {instancePath:instancePath+"/actions/" + i7+"/max_speed_ratio",schemaPath:"#/$defs/motors/properties/max_speed_ratio/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0.05},message:"must be >= 0.05"};
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
const err159 = {instancePath:instancePath+"/actions/" + i7+"/max_speed_ratio",schemaPath:"#/$defs/motors/properties/max_speed_ratio/type",keyword:"type",params:{type: "number"},message:"must be number"};
if(vErrors === null){
vErrors = [err159];
}
else {
vErrors.push(err159);
}
errors++;
}
}
}
else {
const err160 = {instancePath:instancePath+"/actions/" + i7,schemaPath:"#/$defs/motors/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err160];
}
else {
vErrors.push(err160);
}
errors++;
}
var _valid6 = _errs168 === errors;
if(_valid6 && valid60){
valid60 = false;
passing3 = [passing3, 1];
}
else {
if(_valid6){
valid60 = true;
passing3 = 1;
if(props6 !== true){
props6 = true;
}
}
}
if(!valid60){
const err161 = {instancePath:instancePath+"/actions/" + i7,schemaPath:"#/properties/actions/items/oneOf",keyword:"oneOf",params:{passingSchemas: passing3},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err161];
}
else {
vErrors.push(err161);
}
errors++;
}
else {
errors = _errs160;
if(vErrors !== null){
if(_errs160){
vErrors.length = _errs160;
}
else {
vErrors = null;
}
}
}
var valid59 = _errs159 === errors;
}
}
}
else {
const err162 = {instancePath:instancePath+"/actions",schemaPath:"#/properties/actions/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err162];
}
else {
vErrors.push(err162);
}
errors++;
}
}
if(data.privacy !== undefined){
let data64 = data.privacy;
if(data64 && typeof data64 == "object" && !Array.isArray(data64)){
if(data64.school === undefined){
const err163 = {instancePath:instancePath+"/privacy",schemaPath:"#/properties/privacy/required",keyword:"required",params:{missingProperty: "school"},message:"must have required property '"+"school"+"'"};
if(vErrors === null){
vErrors = [err163];
}
else {
vErrors.push(err163);
}
errors++;
}
for(const key17 in data64){
if(!(key17 === "school")){
const err164 = {instancePath:instancePath+"/privacy",schemaPath:"#/properties/privacy/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key17},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err164];
}
else {
vErrors.push(err164);
}
errors++;
}
}
if(data64.school !== undefined){
if(typeof data64.school !== "boolean"){
const err165 = {instancePath:instancePath+"/privacy/school",schemaPath:"#/properties/privacy/properties/school/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err165];
}
else {
vErrors.push(err165);
}
errors++;
}
}
}
else {
const err166 = {instancePath:instancePath+"/privacy",schemaPath:"#/properties/privacy/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err166];
}
else {
vErrors.push(err166);
}
errors++;
}
}
}
else {
const err167 = {instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err167];
}
else {
vErrors.push(err167);
}
errors++;
}
validate20.errors = vErrors;
return errors === 0;
}
validate20.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

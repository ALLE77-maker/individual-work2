import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation, PresentationFile} from '@oai/artifact-tool';
process.env.RUNTIME_NODE_MODULES='/Users/alle/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';

const ROOT=path.resolve(import.meta.dirname,'..');
const SKILL='/Users/alle/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations';
const PY='/Users/alle/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')).href);
const content=JSON.parse(await fs.readFile(path.join(ROOT,'deliverables/slides_content.json'),'utf8'));
const summary=JSON.parse(await fs.readFile(path.join(ROOT,'results/main/summary.json'),'utf8'));
const fix=JSON.parse(await fs.readFile(path.join(ROOT,'results/state_fix/summary.json'),'utf8'));
const p=Presentation.create({slideSize:{width:1280,height:720}});
const FONT='Arial';
const ink='#102D44',muted='#486476',blue='#2675A5',teal='#15897F';

function text(slide,value,x,y,w,h,size=28,bold=false,color=ink){
  const s=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  s.text=value;
  s.text.style={typeface:FONT,fontSize:size,bold,color};
  return s;
}
function table(slide,values,x,y,w,h,widths){
  const t=slide.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,columnWidths:widths,values});
  for(let r=0;r<values.length;r++) for(let c=0;c<values[0].length;c++){
    const cell=t.getCell(r,c);
    cell.text.style={typeface:FONT,fontSize:r===0?22:23,color:ink,bold:r===0};
    cell.fill=r===0?'#E5EEF3':'#FFFFFF';
  }
  t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({margins:{left:14,right:14,top:14,bottom:14},anchor:'center'});
  t.borders.assign({style:'solid',fill:'#CDDBE4',width:1});
  return t;
}
const pct=x=>`${(x*100).toFixed(2)}%`;
const group=summary.conditions;
const q=(condition,key)=>`${group[condition][key].mean.toFixed(2)} ± ${group[condition][key].sample_sd.toFixed(2)}`;
for(const [i,entry] of content.entries()){
  const slide=p.slides.add();
  slide.background.fill='#FFFFFF';
  text(slide,entry.title,72,52,1136,110,i===0?54:41,true);
  if(i===0){
    text(slide,entry.subtitle,74,215,1000,120,34,false,muted);
    text(slide,entry.body.join('\n'),74,430,1000,120,28,false,muted);
    text(slide,'60 live episodes. A separate paired replay of one state fix.',74,604,1080,42,25,true,teal);
  }else if(entry.type==='results'){
    const chart=slide.charts.add('bar',{
      position:{left:80,top:198,width:1110,height:365},
      categories:summary.seeds.map(String),
      series:[
        {name:'Original accessor',values:fix.metrics.original_character_accuracy.trial_values,fill:blue},
        {name:'Preserving accessor',values:fix.metrics.fixed_character_accuracy.trial_values,fill:teal},
      ],
      barOptions:{direction:'column',grouping:'clustered',gapWidth:130},
      hasLegend:true,legend:{position:'bottom',textStyle:{typeface:FONT,fontSize:20}},
      xAxis:{title:'Trial seed',textStyle:{typeface:FONT,fontSize:21}},
      yAxis:{title:'Final character accuracy',min:0,max:0.035,majorUnit:0.01,numberFormatCode:'0.0%',textStyle:{typeface:FONT,fontSize:20},majorGridlines:{fill:'#DCE5EB',width:1}},
      dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.0%',textStyle:{typeface:FONT,fontSize:20}},
      chartFill:'#FFFFFF',plotAreaFill:'#FFFFFF',
    });
    applyPresentationChartFont(chart,{fontFamily:FONT});
    text(slide,`Mean 0.00% vs ${pct(fix.metrics.fixed_character_accuracy.mean)}. Identical recorded observations, with no new model calls.`,82,602,1110,62,24,false,muted);
  }else if(entry.type==='efficiency'){
    table(slide,[
      ['Replay metric','Original accessor','Preserving accessor'],
      ['Affected boards retained','0 / 8','8 / 8'],
      ['Final character accuracy','0.00%',pct(fix.metrics.fixed_character_accuracy.mean)],
      ['Final word accuracy','0.00%','0.00%'],
      ['Terminal error episodes','30 / 30','30 / 30'],
      ['New model calls for replay','0','0'],
    ],76,196,1128,380,[500,314,314]);
    text(slide,'30 paired offline replays. The fix preserves observations and failure status.',80,608,1110,55,23,false,muted);
  }else if(entry.type==='case'){
    const pair=fix.illustrative_pair;
    const board=state=>state.match(/Current Board:\n((?:[A-Z_]{5}\n){5})/)[1].trim().split('\n');
    const grids=[board(pair.original_final_state),board(pair.fixed_final_state),pair.ground_truth_rows];
    const names=['Original accessor','Preserving accessor','Ground truth'];
    for(let j=0;j<3;j++){
      text(slide,names[j],82+386*j,198,350,48,27,true);
      table(slide,grids[j].map(row=>row.split('')),82+386*j,258,350,270,[70,70,70,70,70]);
    }
    text(slide,`${pct(pair.original_character_accuracy)} character accuracy`,82,548,350,50,23,false,blue);
    text(slide,`${pct(pair.fixed_character_accuracy)} character accuracy`,468,548,350,50,23,false,teal);
    text(slide,'Four observed placements precede the terminal error. Complete-word accuracy remains zero.',82,610,1110,60,22,false,muted);
  }else{
    let y=195;
    const body=entry.body??[];
    for(let n=0;n<body.length;n++){
      const isLong=body[n].length>170;
      text(slide,body[n],84,y,1100,isLong?180:94,isLong?29:30,false,n===0&&i!==4?blue:ink);
      y+=isLong?220:112;
    }
  }
  if(i>0) text(slide,`${i+1} / ${content.length}`,1140,678,90,24,16,false,muted);
  slide.speakerNotes.text=entry.notes;
}

const build=path.join(ROOT,'.build');
await fs.mkdir(path.join(build,'slides'),{recursive:true});
for(const [i,slide] of p.slides.items.entries()){
  const png=await p.export({slide,format:'png',scale:1});
  await fs.writeFile(path.join(build,'slides',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
const candidate=path.join(build,'candidate.pptx');
await(await PresentationFile.exportPptx(p)).save(candidate);
const result=await finalizePresentation({
  workspaceDir:ROOT,candidatePath:candidate,
  finalPath:path.join(ROOT,'deliverables/Reproducibility_Presentation.pptx'),
  pythonExecutable:PY,
  integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit','--require-native-table-slide','7','--require-native-table-slide','8'],
  explicitTotalSlideCount:10,
  requiredNativeTableOwnerSlides:[7,8],
  requiredNativeChartOwnerSlides:[6],
  materializeLiteralChartWorkbooks:true,
  fontPolicy:{basis:'design',families:[FONT]},
  verifyArtifactToolImport:true,
  receiptPath:path.join(build,'presentation.validation.json'),
});
console.log(JSON.stringify(result));

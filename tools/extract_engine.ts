import fs from 'node:fs';
import path from 'node:path';
import ts from '../repo/node_modules/typescript/lib/typescript.js';
import * as constants from '../repo/lib/ziwei/constants';
import * as heming from '../repo/lib/ziwei/heming-knowledge';
import { SCHOOL_DEFAULT_CONFIG } from '../repo/lib/ziwei/school-config';
import { ALL_BOOKS } from '../repo/lib/classics/index';
import { PROVINCES } from '../repo/lib/ziwei/cities';
const root=path.resolve('..');
const relative='lib/ziwei/patterns.ts';
const text=fs.readFileSync(path.join(root,'repo',relative),'utf8');
const source=ts.createSourceFile(relative,text,ts.ScriptTarget.Latest,true);
const rules=[];
for(const node of source.statements){
  if(!ts.isFunctionDeclaration(node)||!node.name?.text.startsWith('detect')||node.name.text==='detectPatterns')continue;
  const names:string[]=[];
  function values(n:ts.Node):string[]{
    if(ts.isStringLiteral(n))return [n.text];
    if(ts.isConditionalExpression(n))return [...values(n.whenTrue),...values(n.whenFalse)];
    return [];
  }
  function visit(n:ts.Node){
    if(ts.isPropertyAssignment(n)&&n.name.getText(source)==='name'){
      names.push(...values(n.initializer));
    }
    ts.forEachChild(n,visit);
  }
  visit(node);
  const line=source.getLineAndCharacterOfPosition(node.getStart(source)).line+1;
  rules.push({function:node.name.text,names:[...new Set(names)],line,source_code:node.getFullText(source).trim(),source_path:relative});
}
const result={constants,heming,rules,school_defaults:SCHOOL_DEFAULT_CONFIG,curated_classics:ALL_BOOKS,cities:PROVINCES};
fs.writeFileSync(path.join(root,'sources/supplementary/engine-knowledge.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify({rules:rules.length,constants:Object.keys(constants),heming:Object.keys(heming)}));

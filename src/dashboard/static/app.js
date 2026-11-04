'use strict';
let token='',tab='general',paused=false,data=[];
const routes={general:'runtime/resources',logs:'logs',jobs:'jobs',operations:'operations',campaigns:'campaigns',models:'models',services:'health/services',infra:'runtime/resources'};
const el=id=>document.getElementById(id);
async function refresh(){
 if(!token||paused)return;
 const requestedTab=tab,params=new URLSearchParams();
 if(tab==='logs') for(const id of ['namespace','service','pod','level','correlation_id','q','since','until']) if(el(id).value)params.set(id,el(id).value);
 try{
  const response=await fetch('/api/'+routes[tab]+'?'+params,{headers:{Authorization:'Bearer '+token},signal:AbortSignal.timeout(15000)});
  if(!response.ok)throw new Error('Consulta indisponível (HTTP '+response.status+'). Verifique token e serviços.');
  const result=await response.json();if(tab!==requestedTab)return;
  data=Array.isArray(result)?result:Object.entries(result).map(([service,status])=>({service,status}));
  el('content').replaceChildren();
  if(!data.length){el('content').textContent='Nenhum registro encontrado.';}else{
   const table=document.createElement('table'),head=document.createElement('tr');const keys=[...new Set(data.flatMap(Object.keys))];
   for(const key of keys){const cell=document.createElement('th');cell.textContent=key;head.append(cell);}table.append(head);
   for(const row of data){const tr=document.createElement('tr');for(const key of keys){const cell=document.createElement('td');cell.textContent=typeof row[key]==='object'?JSON.stringify(row[key]):String(row[key]??'—');tr.append(cell);}table.append(tr);}el('content').append(table);
  }
  el('status').textContent='Atualizado '+new Date().toLocaleTimeString('pt-BR')+' · '+data.length+' registros';
 }catch(error){el('status').textContent=error.message;}
}
el('login').onsubmit=event=>{event.preventDefault();token=el('token').value;el('token').value='';refresh();};
document.querySelectorAll('[data-tab]').forEach(button=>button.onclick=()=>{tab=button.dataset.tab;el('filters').hidden=tab!=='logs';document.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('active',b===button));refresh();});
el('pause').onclick=()=>{paused=!paused;el('pause').textContent=paused?'Retomar':'Pausar';refresh();};
el('export').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='logs-poc.json';link.click();URL.revokeObjectURL(url);};
el('filters').onchange=refresh;setInterval(refresh,10000);

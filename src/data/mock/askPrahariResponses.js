export const askPrahariResponses={
 'why is the schedule at risk':{answer:'Physical progress is below the planned trajectory, the revised completion date moved, and two milestone checkpoints show slippage.',evidence:'Monthly Progress Report · June 2026'},
 'which milestone is delayed':{answer:'Mid Execution is recorded as delayed, while Major Completion remains at risk against the revised timeline.',evidence:'Milestone evidence snapshot · June 2026'},
 'what is the latest cost status':{answer:'Latest revised cost is ₹3,980 Cr and cumulative expenditure is ₹2,104 Cr. A verified final-cost forecast is not available.',evidence:'Project cost summary · June 2026'},
 'show key concerns':{answer:'Current concerns are slower physical progress, timeline movement, milestone slippage and expenditure-to-progress alignment.',evidence:'Unified project intelligence demo record'},
 'what are the key risks for this project':{answer:'The research preview highlights schedule slippage, cost pressure, milestone delay and expenditure-to-progress misalignment. These are decision-support signals, not confirmed causes.',evidence:'Unified project intelligence demo record'},
 'summarize this project':{answer:'Bhatadi Expansion OC is under implementation with 62% reported physical progress, a revised completion date of December 2026 and Execution Health under watch.',evidence:'Project dossier · June 2026'},
 'what action should i review first':{answer:'First verify the latest completion-date movement and the supporting milestone evidence with the implementing agency.',evidence:'Recommended Officer Action · project dossier'},
 'summarize projects needing attention':{answer:'The demo queue prioritizes Bhatadi Expansion OC, Mumbai High platform works and Pachwara South Coal Block for schedule, cost or evidence review.',evidence:'Officer Attention Queue · June 2026'},
 'which projects need attention':{answer:'The demo queue prioritizes Bhatadi Expansion OC, Mumbai High platform works and Pachwara South Coal Block for schedule, cost or evidence review.',evidence:'Officer Attention Queue · June 2026'},
 'show high concern projects':{answer:'The High Concern saved view includes projects with elevated schedule or cost states. Open Projects and select High concern to inspect the filtered list.',evidence:'Projects saved view · local demo data'},
 'how many projects need data verification':{answer:'The curated frontend dataset contains projects explicitly marked Needs verification. Use the Data Quality filter to see the exact demonstration records.',evidence:'Projects Data Quality filter · local demo data'},
 'what changed this month':{answer:'The demonstration portfolio includes a revised-cost update, a new report, one completed review and one source-verification flag.',evidence:'Portfolio recent updates · June 2026'},
 'show reviews assigned to me':{answer:'Five curated reviews are available in this demo. Bhatadi Expansion OC is the highest-priority action-required case.',evidence:'Officer Review Queue · local demo state'},
 'why was this alert raised':{answer:'This alert was raised by governed demonstration policy after an Officer Decision recommendation, using milestone delay and progress evidence. It was not created directly from a raw probability.',evidence:'Alert evidence snapshot · governed demo contract'},
 'what evidence supports this alert':{answer:'The evidence snapshot includes the May 2026 source report, project identity, pages 14–16, approved timeline and reported physical progress.',evidence:'Alert evidence snapshot · May 2026'},
 'what should i do next':{answer:'Open the evidence pack, confirm the source and milestone movement, then acknowledge or assign a review. The officer remains the decision-maker.',evidence:'Recommended officer workflow'},
 'what should the officer do next':{answer:'Open the evidence pack, confirm the source and milestone movement, then acknowledge or assign a review. The officer remains the decision-maker.',evidence:'Recommended officer workflow'},
 'summarize this review':{answer:'The review is tracking evidence confirmation, agency follow-up, progress variance and the next reporting checkpoint. Notes and actions are preserved in local demo state.',evidence:'Review workflow · local demo state'},
 'what actions are pending':{answer:'Pending actions may include checking progress variance, scheduling a follow-up and recording the review outcome. The checklist on the review page is authoritative for this demo session.',evidence:'Review recommended-actions checklist'},
 'what evidence has been checked':{answer:'The demonstration review tracks source submission, monthly progress evidence, timeline movement and officer notes. Completed checklist items show what has been checked.',evidence:'Review evidence pack · local demo state'},
};

export const contextPrompts={
 project:['Why is the schedule at risk?','Which milestone is delayed?','What is the latest cost status?','What are the key risks for this project?','Summarize this project.','What action should I review first?'],
 alert:['Why was this alert raised?','What evidence supports this alert?','What should the officer do next?'],
 review:['Summarize this review.','What actions are pending?','What evidence has been checked?'],
 portfolio:['Which projects need attention?','Show high concern projects.','How many projects need data verification?','What changed this month?'],
};

export function resolveDemoQuestion(question){
 const normalized=question.toLowerCase().replace(/[?.!,]/g,'').replace(/\s+/g,' ').trim();
 const exact=askPrahariResponses[normalized];if(exact)return exact;
 const key=Object.keys(askPrahariResponses).find(k=>normalized.includes(k)||k.includes(normalized));
 return key?askPrahariResponses[key]:{answer:'I can answer the curated questions shown above for this deterministic demonstration. For other questions, open the relevant project, alert or review evidence rather than inferring an unsupported answer.',evidence:'Safe deterministic fallback · no live model call'};
}

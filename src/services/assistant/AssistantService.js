import { resolveDemoQuestion } from '../../data/mock/askPrahariResponses';

export class AssistantService { async ask(){throw new Error('AssistantService.ask must be implemented')} }
export class DemoAssistantService extends AssistantService {async ask({question,context}){await new Promise(resolve=>window.setTimeout(resolve,600+Math.floor(Math.random()*251)));return {...resolveDemoQuestion(question),context}}}
export class ApiAssistantService extends AssistantService {constructor(endpoint){super();this.endpoint=endpoint}async ask(payload){const response=await fetch(this.endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(!response.ok)throw new Error('Assistant service unavailable');return response.json()}}
export const assistantService=new DemoAssistantService();

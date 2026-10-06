import { handleNewsletter } from './newsletter.mjs';
const env = Object.fromEntries(['SUPABASE_URL','RTA_GATEWAY_KEY','RESEND_API_KEY'].map(key => [key,Deno.env.get(key)]));
Deno.serve(request => handleNewsletter(request,env));

import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createRequire, stripTypeScriptTypes } from 'node:module';
import { pathToFileURL } from 'node:url';
const require=createRequire(import.meta.url);
const nextServer=pathToFileURL(require.resolve('next/server.js')).href;
const {NextRequest}=await import(nextServer);
async function handler(path) {
 const source=await readFile(new URL(path,import.meta.url),'utf8');
 const js=stripTypeScriptTypes(source).replace('"next/server"',JSON.stringify(nextServer));
 return (await import(`data:text/javascript;base64,${Buffer.from(js).toString('base64')}`)).GET;
}
const start=await handler('../../app/api/auth/google/route.ts');
const callback=await handler('../../app/api/auth/callback/google/route.ts');

test('Google authorization requests a code and binds a random state cookie',async()=>{
 const previous=process.env.GOOGLE_CLIENT_ID;process.env.GOOGLE_CLIENT_ID='test-client';
 try {
  const result=await start(new NextRequest('http://localhost:3050/api/auth/google?from=/admin'));
  const url=new URL(result.headers.get('location'));
  assert.equal(url.origin,'https://accounts.google.com');
  assert.equal(url.searchParams.get('response_type'),'code');
  assert.equal(url.searchParams.get('client_id'),'test-client');
  assert.equal(url.searchParams.get('state'),result.cookies.get('oauth_state').value);
  assert.ok(result.cookies.get('oauth_state').value.length>=32);
  assert.equal(result.cookies.get('oauth_from').value,'/admin');
 } finally {if(previous===undefined)delete process.env.GOOGLE_CLIENT_ID;else process.env.GOOGLE_CLIENT_ID=previous;}
});

test('callback rejects missing or mismatched state before exchanging a code',async()=>{
 const original=globalThis.fetch;let calls=0;
 globalThis.fetch=async()=>{calls++;return Response.json({access_token:'test-token'});};
 try {
  for(const cookie of ['', 'oauth_state=another-state']) {
   const response=await callback(new NextRequest('http://localhost:3050/api/auth/callback/google?code=test&state=expected',{headers:{cookie}}));
   assert.equal(new URL(response.headers.get('location')).searchParams.get('error'),'invalid_state');
  }
  assert.equal(calls,0);
 } finally {globalThis.fetch=original;}
});

test('valid callback exchanges code, restores admin destination and consumes state',async()=>{
 const original=globalThis.fetch;
 globalThis.fetch=async(url,options)=>{
  assert.equal(JSON.parse(options.body).code,'test-code');
  return Response.json({access_token:'test-token',user:{id:'test-user'}});
 };
 try {
  const response=await callback(new NextRequest('http://localhost:3050/api/auth/callback/google?code=test-code&state=expected',{headers:{cookie:'oauth_state=expected; oauth_from=/admin'}}));
  const url=new URL(response.headers.get('location'));
  assert.equal(url.pathname,'/callback');assert.equal(url.searchParams.get('from'),'/admin');
  assert.equal(response.cookies.get('auth_token').value,'test-token');
  assert.equal(response.cookies.get('oauth_state').value,'');
 } finally {globalThis.fetch=original;}
});

test('basic sign-in never requests Sheets, Drive or offline consent',async()=>{
 const previous=process.env.GOOGLE_CLIENT_ID;process.env.GOOGLE_CLIENT_ID='test-client';
 try {
  const response=await start(new NextRequest('http://localhost:3050/api/auth/google'));
  const url=new URL(response.headers.get('location'));
  assert.equal(url.searchParams.get('scope'),'openid email profile');
  assert.equal(url.searchParams.has('access_type'),false);
  assert.equal(url.searchParams.has('include_granted_scopes'),false);
  assert.equal(url.searchParams.get('prompt'),'select_account');
 } finally {if(previous===undefined)delete process.env.GOOGLE_CLIENT_ID;else process.env.GOOGLE_CLIENT_ID=previous;}
});

test('explicit Sheets consent binds current app user and requests no Drive scope',async()=>{
 const previous=process.env.GOOGLE_CLIENT_ID;process.env.GOOGLE_CLIENT_ID='test-client';
 const original=globalThis.fetch;
 globalThis.fetch=async(_url,options)=>{assert.equal(options.headers.Authorization,'Bearer app-session');return Response.json({id:'owner'});};
 try {
  const response=await start(new NextRequest('http://localhost:3050/api/auth/google?intent=sheets',{headers:{cookie:'auth_token=app-session'}}));
  const url=new URL(response.headers.get('location'));
  assert.equal(url.searchParams.get('scope'),'openid email profile https://www.googleapis.com/auth/spreadsheets');
  assert.equal(response.cookies.get('oauth_connection_user').value,'owner');
  assert.equal(response.cookies.get('oauth_intent').value,'sheets');
 } finally {globalThis.fetch=original;if(previous===undefined)delete process.env.GOOGLE_CLIENT_ID;else process.env.GOOGLE_CLIENT_ID=previous;}
});

test('Sheets callback preserves login session and connects only authenticated owner',async()=>{
 const original=globalThis.fetch;
 globalThis.fetch=async(url,options)=>{
  assert.ok(url.endsWith('/auth/google/connect'));
  assert.equal(options.headers.Authorization,'Bearer app-session');
  assert.equal(JSON.parse(options.body).expected_user_id,'owner');
  return Response.json({connected:true});
 };
 try {
  const response=await callback(new NextRequest('http://localhost:3050/api/auth/callback/google?code=test&state=expected',{headers:{cookie:'oauth_state=expected; oauth_intent=sheets; oauth_connection_user=owner; auth_token=app-session'}}));
  assert.equal(new URL(response.headers.get('location')).searchParams.get('google_connection'),'success');
  assert.equal(response.cookies.has('auth_token'),false);
  assert.equal(response.cookies.get('oauth_connection_user').value,'');
 } finally {globalThis.fetch=original;}
});

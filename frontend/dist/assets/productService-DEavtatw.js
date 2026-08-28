import{c,N as s}from"./index-C71cZeBV.js";/**
 * @license lucide-react v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const p=c("CalendarClock",[["path",{d:"M21 7.5V6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h3.5",key:"1osxxc"}],["path",{d:"M16 2v4",key:"4m81vk"}],["path",{d:"M8 2v4",key:"1cmpym"}],["path",{d:"M3 10h5",key:"r794hk"}],["path",{d:"M17.5 17.5 16 16.3V14",key:"akvzfd"}],["circle",{cx:"16",cy:"16",r:"6",key:"qoo3c4"}]]);async function r(a={}){return(await s.get("/products",{params:a})).data}async function i(a){return(await s.get(`/products/${encodeURIComponent(a)}`)).data}function u(a,t="Product information could not be loaded."){var o,n;const e=(n=(o=a==null?void 0:a.response)==null?void 0:o.data)==null?void 0:n.detail;return typeof e=="string"?e:t}export{p as C,u as a,i as b,r as g};

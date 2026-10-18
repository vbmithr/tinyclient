import json,re,pathlib,sys
T=json.load(open(sys.argv[1]))
out=pathlib.Path(sys.argv[2])
base='https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/'
def snake(s):return re.sub(r'([a-z0-9])([A-Z])',r'\1_\2',re.sub(r'([A-Z]+)([A-Z][a-z])',r'\1_\2',s)).lower()
def attrval(attrs,k):
 m=re.search(r'\b'+k+r'\s*=\s*"([^"]+)"',' '.join(attrs));return m[1] if m else None
def name(v,attrs):return attrval(v.get('serde',[]),'rename') or (v['name'].lower() if attrval(attrs,'rename_all')=='lowercase' else snake(v['name']) if attrval(attrs,'rename_all')=='snake_case' else v['name'])
def clean(s):return re.sub(r'\[`([^`]+)`\]',r'`\1`',s).replace('|','\\|')
def typ(s):
 s=re.sub(r'\s+','',s)
 if s.startswith('Box<'):return typ(s[4:-1])
 for p,label in [('Option<','nullable'),('Vec<','list')]:
  if s.startswith(p):return label+'<'+typ(s[len(p):-1])+'>'
 if s.startswith('('):return 'tuple('+','.join(typ(x) for x in s[1:-1].split(','))+')'
 return {'String':'string','bool':'boolean','u8':'uint8','u16':'uint16','u32':'uint32','u64':'uint64','i32':'int32','i64':'int64','usize':'uint(platform)','f32':'float32','f64':'float64'}.get(s,s)
def fieldtable(b):
 if not b['fields']:return ['No payload fields.','']
 lines=['| Field | JSON type | Missing field | Serialization notes |','| --- | --- | --- | --- |']
 for f in b['fields']:
  a=' '.join(f['serde']);tt=typ(f['type']);optional=bool(re.search(r'\bdefault\b',a)) or tt.startswith('nullable<');d=attrval(f['serde'],'default');missing=('true' if d=='yes' else 'type default') if re.search(r'\bdefault\b',a) else 'null' if tt.startswith('nullable<') else '**error**'
  skip=attrval(f['serde'],'skip_serializing_if');notes=[]
  if 'flatten' in a:notes.append('merge referenced object fields into parent; no field named '+f['name'])
  if skip:notes.append('omit when `'+skip+'` is true')
  lines.append('| `'+f['name']+'` | `'+tt+'` | '+missing+' | '+('; '.join(notes) or 'emit normally')+' |')
  if f['doc']:lines.append('| | | | '+clean(f['doc'])+' |')
 return lines+['']
lines=['# Chatd IPC type catalogue','','Companion to [the IPC specification](chatd-ipc.md). Extracted from all 94','top-level serializable protocol types at upstream commit `7b98c4c`, including','68 request variants, 30 response variants and 19 change variants. Names in','backticks are symbolic types, not a requirement to use Rust. This catalogue','also includes media-helper types; only `Request` is accepted on `chat.sock`.','','## Reading the catalogue','','`uintN` and `intN` are JSON integers of the stated width; `floatN` is a finite','JSON number. `list<T>` is an array; `tuple(A,B)` is a fixed-length JSON array.','`nullable<T>` accepts null or the referenced value. `Box<T>` has no wire effect.','`usize`, where present, is bounded by the reference platform; do not infer a','portable wire width from it. Object field order is insignificant.','','An **error** in the Missing field column means the reference decoder requires','the field. A field that accepts null is not necessarily omitted by the encoder.','Type defaults, custom defaults and omission predicates are explained in the','specification. Each type links to the exact source; descriptive source comments','are included, but runtime limits and side effects come from the specification.','','The following predicate names preserve the reference implementation terminology:','`Option::is_none` means null/absent; `Vec::is_empty` means `[]`;','`String::is_empty` means `""`; `is_false`/`Not::not` mean false; `is_true` means','true; `is_zero`/`is_zero64` mean zero. Enum predicates such as `is_sent`,','`is_normal`, `is_section`, `is_main` and `is_any` select their named default','variant. `Capabilities::is_none` and `Keychain::is_settled` are defined in the','linked source and covered by the defaults section of the specification.','']
ordered=sorted(T,key=lambda t:({'Request':0,'Response':1,'Change':2}.get(t['name'],3),t['name']))
for t in ordered:
 lines+=['## '+t['name'],'','[Source]('+base+t['source']+').','']
 if t['doc']:lines += [clean(t['doc']),'']
 if t['kind']=='struct':
  lines+=['JSON object.','']+fieldtable(t['body'])
 else:
  tag=attrval(t['serde'],'tag')
  lines += [('Internally tagged object: discriminator `'+tag+'`.') if tag else 'Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.','']
  for v in t['body']:
   wire=name(v,t['serde']);b=v['body'];lines+=['### '+wire,'']
   if v['default']:lines+=['Default variant for this type.','']
   if v['doc']:lines += [clean(v['doc']),'']
   if tag:lines += ['Discriminator: `"'+tag+'": "'+wire+'"`.','']
   elif b['shape']=='unit':lines += ['JSON value: `"'+wire+'"`.','']
   else:lines += ['JSON object key: `"'+wire+'"`; its value is the payload below.','']
   if b['shape']=='newtype':
    lines += ['Payload is `'+typ(b['fields'][0]['type'])+'`'+('; merge its object/discriminator fields into this object, without a wrapper field.' if tag else '; no numeric field named `0`.'),'']
   else:lines+=fieldtable(b)
out.write_text('\n'.join(lines))
print(out, len(lines),'lines')

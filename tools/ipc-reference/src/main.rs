use quote::ToTokens;
use serde_json::{json, Value};
use syn::{Attribute, Fields, Item, Meta, Expr, Lit};
fn attrs(a: &[Attribute], name: &str) -> Vec<String> {
    a.iter().filter(|a| a.path().is_ident(name)).map(|a| match &a.meta {
        Meta::List(l) => l.tokens.to_string(), _ => a.meta.to_token_stream().to_string()
    }).collect()
}
fn docs(a: &[Attribute]) -> String {
    a.iter().filter_map(|a| if let Meta::NameValue(n) = &a.meta {
        if n.path.is_ident("doc") { if let Expr::Lit(e) = &n.value {if let Lit::Str(s)=&e.lit{return Some(s.value().trim().to_string());}} }
        None
    } else {None}).collect::<Vec<_>>().join(" ")
}
fn fields(f: &Fields) -> Value {
    let shape=match f {Fields::Named(_)=>"object", Fields::Unnamed(u) if u.unnamed.len()==1=>"newtype",Fields::Unnamed(_)=>"tuple",Fields::Unit=>"unit"};
    json!({"shape":shape,"fields": f.iter().enumerate().map(|(i,f)| json!({"name":f.ident.as_ref().map(|n|n.to_string()).unwrap_or(i.to_string()),"type":f.ty.to_token_stream().to_string(),"serde":attrs(&f.attrs,"serde"),"doc":docs(&f.attrs)})).collect::<Vec<_>>()})
}
fn main() {
    let root=std::env::args().nth(1).unwrap();let mut types=Vec::new();
    for file in ["lib","message","info","call","play","react","settings","signin"] {
        let path=format!("{root}/{file}.rs");let src=std::fs::read_to_string(path).unwrap();
        for item in syn::parse_file(&src).unwrap().items {
            let (id,a,kind,body)=match item {
                Item::Struct(s)=>(s.ident,s.attrs,"struct",fields(&s.fields)),
                Item::Enum(e)=>{let variants=e.variants.iter().map(|v|json!({"name":v.ident.to_string(),"serde":attrs(&v.attrs,"serde"),"default":v.attrs.iter().any(|a|a.path().is_ident("default")),"doc":docs(&v.attrs),"body":fields(&v.fields)})).collect::<Vec<_>>();(e.ident,e.attrs,"enum",json!(variants))},
                _=>continue
            };
            if !attrs(&a,"derive").iter().any(|d|d.split(|c:char|!c.is_alphanumeric()).any(|s|s=="Serialize")) {continue}
            types.push(json!({"name":if file=="settings" {format!("settings::{id}")}else{id.to_string()},"source":format!("crates/protocol/src/{file}.rs"),"kind":kind,"serde":attrs(&a,"serde"),"doc":docs(&a),"body":body}));
        }
    }
    println!("{}",serde_json::to_string_pretty(&types).unwrap());
}

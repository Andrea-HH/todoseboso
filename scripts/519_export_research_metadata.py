"""Export portable research metadata; never fit models or copy data/predictions."""
from pathlib import Path
import ast
import csv
import hashlib
import json
import platform
import re
import subprocess
import sys
from importlib import metadata

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'configs'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False)+'\n', encoding='utf-8', newline='\n')


def csv_write(p, fields, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def portable(obj):
    if isinstance(obj, dict):
        return {portable(k): portable(v) for k,v in obj.items()}
    if isinstance(obj, list):
        return [portable(v) for v in obj]
    if isinstance(obj, str):
        for base, token in [(ROOT, '${REPO_ROOT}'), (ROOT.parent/'fira/GeoC', '${GEOC_ROOT}')]:
            for old in [str(base),base.as_posix(),str(base).replace('\\','/')]:
                if obj.startswith(old):
                    return token+obj[len(old):].replace('\\','/')
    return obj


def export_designs():
    rows=[]
    for source in sorted((ROOT/'outputs/modeling').glob('*/v*/frozen_design.json')):
        relative=source.relative_to(ROOT)
        target=CONFIG/'experiments'/relative.parts[2]/relative.parts[3]/'frozen_design.json'
        dump(target, portable(json.loads(source.read_text(encoding='utf-8'))))
        rows.append(dict(source=relative.as_posix(),snapshot=target.relative_to(ROOT).as_posix(),
                         source_sha256=sha(source),snapshot_sha256=sha(target),
                         note='Portable metadata snapshot; source unchanged. A frozen design does not prove execution.'))
    dump(CONFIG/'experiments/manifest.json',dict(schema_version=1,export_date='2026-10-18',
        path_tokens={'${REPO_ROOT}':'repository root','${GEOC_ROOT}':'optional GeoC repository root'},
        source_policy='Only outputs/modeling/*/v*/frozen_design.json files available locally. Not a complete historic configuration archive.',snapshots=rows))
    return len(rows)


def export_splits():
    # Trusted project-generated local artifacts; no untrusted pickle input.
    import joblib
    import pandas as pd
    train=ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet'
    ids=pd.read_parquet(train,columns=['ID_POLIGONO']).ID_POLIGONO.astype(str).tolist()
    assert len(ids)==len(set(ids))==138
    order_hash=hashlib.sha256(json.dumps(ids,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    sources=[('original65',ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/frozen65_splits.joblib'),
             ('original65_plus_fresh16',ROOT/'outputs/modeling/four_expert_combinations/v1/frozen81_splits.joblib')]
    exported=[]
    for name,source in sources:
        records=[]
        for ix,(protocol,repeat,fold,tr,va,inner) in enumerate(joblib.load(source)):
            tr=list(map(int,tr)); va=list(map(int,va))
            assert not set(tr)&set(va) and sorted(tr+va)==list(range(138))
            internal=[]
            for a,b in inner:
                a=list(map(int,a)); b=list(map(int,b))
                assert not set(a)&set(b) and sorted(a+b)==list(range(len(tr)))
                internal.append(dict(train_relative_positions=a,validation_relative_positions=b))
            records.append(dict(execution_index=ix,protocol=str(protocol),repeat=int(repeat),fold=int(fold),
                                train_positions=tr,validation_positions=va,inner=internal))
        target=CONFIG/'validation'/(name+'.json')
        dump(target,dict(schema_version=1,source=source.relative_to(ROOT).as_posix(),source_sha256=sha(source),
                         train_source=train.relative_to(ROOT).as_posix(),train_source_sha256=sha(train),
                         ordered_ids_sha256=order_hash,ordered_ids_hash_encoding='UTF-8 JSON list, ensure_ascii=False, separators=(comma,colon)',
                         positions='Zero-based in original ordered train138; inner positions relative to corresponding outer train list.',
                         privacy='No IDs, yields, predictors or predictions included.',
                         limit='Deeper residual cross-fitting is implemented in source/context artifacts; not all recursive contexts are serialized here.',
                         folds=records))
        exported.append((name,records))
    assert exported[0][1]==exported[1][1][:65]
    assert len(exported[0][1])==65 and len(exported[1][1])==81


def inventories():
    rows=[]
    for folder in ['scripts','src','tests','documentation']:
        for p in sorted((ROOT/folder).rglob('*')):
            if p.suffix not in ['.py','.md'] or '__pycache__' in p.parts: continue
            text=p.read_text(encoding='utf-8-sig')
            title=''
            if p.suffix=='.py':
                try: title=(ast.get_docstring(ast.parse(text)) or '').split('\n')[0]
                except SyntaxError: title='Requires manual syntax review'
            else:
                title=next((line.lstrip('# ').strip() for line in text.splitlines() if line.startswith('#')),'')
            name=p.name.lower()
            role=('test' if folder=='tests' else 'implementation' if folder=='src' else
                  'frozen design / proposal' if 'design' in name or 'proposal' in name else
                  'results / interpretation' if any(t in name for t in ['result','conclusion','decision']) else
                  'execution helper / entry point' if folder=='scripts' else 'documentation')
            rows.append(dict(path=p.relative_to(ROOT).as_posix(),area=folder,role=role,title=title,
                             execution_status='Not inferred from file existence'))
    csv_write(ROOT/'documentation/inventories/repository_files.csv',list(rows[0]),rows)


def environment():
    roots=set()
    for folder in ['src','scripts','tests']:
        for p in (ROOT/folder).rglob('*.py'):
            try: tree=ast.parse(p.read_text(encoding='utf-8-sig'))
            except (SyntaxError,UnicodeError): continue
            for n in ast.walk(tree):
                if isinstance(n,ast.Import): roots.update(a.name.split('.')[0] for a in n.names)
                elif isinstance(n,ast.ImportFrom) and n.module and n.level==0: roots.add(n.module.split('.')[0])
    mapping=metadata.packages_distributions()
    packages={d:metadata.version(d) for r in sorted(roots) if r not in sys.stdlib_module_names for d in mapping.get(r,[])}
    dump(ROOT/'environments/research_environment.json',dict(snapshot_date='2026-10-18',python=platform.python_version(),
        platform=platform.system(),method='Installed distributions mapped from statically detected imports in src/scripts/tests.',
        limitation='Observed environment, not a clean-install validation or full transitive lock; dynamic imports may be absent.',
        direct_import_distributions=packages,
        unresolved_import_roots=sorted(r for r in roots if r not in sys.stdlib_module_names and r not in mapping and r not in ['src','tests'])))
    (ROOT/'requirements-research.txt').write_text(
        '# Observed research dependencies; see environments/README.md. Not a verified transitive lock.\n'+
        '\n'.join(f'{name}=={version}' for name,version in sorted(packages.items(),key=lambda t:t[0].lower()))+'\n',encoding='utf-8')


PROMPTS=[
('rainfall','e47501b5-9ee8-4567-b583-057e089d8997','Modelado lluvia y evaluación inicial','rainfall_yield_modeling.md'),
('rainfall_pca','49655eef-0db7-4cf7-ac49-346887258f08','PCA y PCR de lluvia','rainfall_yield_modeling.md'),
('climate_GH','c8475b26-857d-4988-bc4e-e46e6333586d','Complementariedad climática','g_h_climate_signal_exploration.md'),
('soil_I','e11e0295-8831-4b4d-ac8a-1f384bb4a39a','Exploración geográfica y edafológica','i_geographic_edaphological_exploration.md'),
('incremental_J','98a3cb90-8ce3-4e25-ad88-1445d16fdba3','Información incremental física','j_incremental_yield_modeling.md'),
('soil_K','9faa7bdc-5869-4c78-9f0c-f24c062257b0','Rediseño del modelado de suelo','k_decision_summary.md'),
('multiblock_LM','7d007e6b-602c-4814-918d-886b9674250b','Representaciones multibloque e historia','l_m_synthesis.md'),
('conditional_F4','4e37b891-9b36-4d74-a699-80730bf120fb','Sensibilidades condicionales','family4_conditional_yield_response.md'),
('intraprofile_F4','cac0b138-4b7f-4c55-9d49-2374aa3a4136','Complementariedad intraperfil','family4_e_within_profile_complementarity.md'),
('territorial_A','30789fb3-c856-4b4f-b146-a3894ecd3975','Programa de heterogeneidad y transferencia','territorial_program_stage_a.md'),
('territorial_B','fa6905c8-d270-4aaf-8a6d-886c78914d67','Aprendizaje intraperfil y ensambles','territorial_program_stage_b.md'),
('territorial_C','3abdeec5-2b6e-4a46-9be9-e59152c4d8e9','Modelos jerárquicos y representación','territorial_program_stage_c.md'),
('territorial_D','d79ca06e-c004-4a9e-88e4-9386a17fb30b','Síntesis y diagnóstico de generalización','territorial_program_stage_d_executive.md'),
('GPR_F5','816314cb-47f0-4c49-aab5-b84ad0d0a17e','Auditoría y diseño de Gaussian Processes','family5_gpr_technical_proposal.md'),
('bagging_F6','08356867-58df-4897-ad8b-3d26cc4f4d92','Random Forest y Extra Trees','family6_bagging.md'),
('expansion_F6','27179e20-959e-4ee4-8a2e-6087df7a753c','Historia y pendiente para árboles','family6_expansion.md'),
('expansion_F7','e324b969-1d3d-4325-9a64-904c5767dc57','Ablaciones de CatBoost','family7_expansion.md'),
('proposal_F8','79353671-267d-44f0-8a90-edca0d128d59','Auditoría de hipótesis residuales; no prueba ejecución','family8_recommendation.md'),
('incremental_CT3','904abca5-ee4b-4230-817a-b7e7f84edb2b','Información condicionada a C-T3','ct3_incremental_information_findings.md'),
('representations_CT3','695669e9-5f4d-49c4-913d-1303cb552303','Representaciones complementarias','ct3_information_phase_iii.md'),
('residual_CT3','83d4bd08-d8ec-4784-b1d3-167402a39178','Diseño de corrección residual condicional','ct3_residual_conditional.md'),
]


def prompts():
    rows=[]
    for i,(slug,attachment,purpose,evidence) in enumerate(PROMPTS,1):
        source=Path.home()/'.codex/attachments'/attachment/'Pasted text.txt'
        if not source.exists():
            raise FileNotFoundError(f'Prompt source unavailable: {attachment}')
        target=ROOT/'documentation/ai/prompts'/f'P{i:03d}_{slug}.txt'
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(source.read_bytes())
        rows.append(dict(prompt_id=f'P{i:03d}',tool='Codex (asistente de IA generativa)',model='No registrado de forma verificable para este intercambio',
                         date='Fecha histórica no recuperada',purpose=purpose,transcription='Literal: adjunto original conservado byte por byte',
                         source='Adjunto del usuario '+attachment,prompt_file=target.relative_to(ROOT).as_posix(),sha256=sha(target),
                         related_document='documentation/'+evidence,execution_caveat='La solicitud no prueba que se ejecutara todo lo pedido; consultar resultados/decisiones.'))
    messages=[
        ('quiero por explorar hacer un arbol con todass las variables quiero ver que pasa','Explorar árbol con representación completa','experimental_tree1867.md'),
        ('por saber puedes hacerme un modelo de pls que parta de las 1867 variables es mero exmeriento','Explorar PLS de alta dimensión','experimental_pls1867.md'),
        ('okay aplica las correcciones y corre la investigación','Revisar y ejecutar investigación residual con alcance corregido','ct3_residual_conditional.md'),
        ('en este repo quiero hacer mis comparacioens y pruebas de combinacion de los 2 modelos','Comparación C-T3 y GeoC/Local04D','geoc_bridge_results.md'),
        ('quiero que el ridge no sea climatologico porque ya vimos que eso se queda corto que sua geograficamente el l40 eso es loq ue queiro combinar con ct3','Separar señal local no climática y núcleo compacto','nonclimatic_local_results.md'),
        ('se hizo una exploracion exaustiva de los compenentes y señales fisicas y una reduccion de dimensionalidad de ellos apra saber si es lo optimo','Revisar representaciones físicas','physical_representation_results.md'),
        ('realiza los experimentos para poder determinar como lograr la menor perdida de informacion y si e sposible incluso alternar roles par aver si esto ayuda o empera o no se ocmo plantear como qquitar de main pero posible que aporten como correctores','Ablaciones y asignación de funciones','signal_role_allocation_results.md'),
        ('dame una evaaluacion completa de residuos de este modelo','Diagnosticar errores y regiones','j7_both_residual_audit.md'),
        ('quiza no regla de arbol si no utlizar la señal de diferencia con el el grupo general como una de las variable pero para aplicacion de correccion o se la señal','Construir contrastes con vecinos','neighbor_signal_linear_conclusions.md'),
        ('no simplificacion del corrector simplificacion del modleo base e incluso usar el correcto sobre el mas basico qie era ct3 explorar combinaciones','Separar simplificación de base y corrector','j7_r3_simplification_research.md'),
        ('realiza los experimentos propuestos y las diferentes descompsicions y combinaciones','Descomponer arquitecturas y evaluar ablaciones','architecture_decomposition_conclusions.md'),
        ('realiza la investigacion modelado y comparacion concecuente','Ejecutar batería de combinaciones previamente discutida','four_expert_combinations_conclusions.md'),
        ('mi repositorio tiene  orden ? hay algo que no este claro o se necesite limpiar?','Auditar organización, documentación y Git','repository_organization.md'),
        ('okay haz un read me basado en en los documentos de lineamientos lo que quiero es que sea muy claro el aim de proyecto es generar un modelo para ese proposito  luefgo apra esta distincion no se en que parte sea prudente pero queiro un readme que explique los modleos que existen y cuales estan en que parte y porque tambien haz la tranformacion para el versionado para el indice de experimentos quieor que se quede bien la documentacon como dices la coumentacon clara tmabien queiro que haya una seccion de documetnacion dodnde se haga como un inventario de como se utlizo en el repo ia generativa','Reorganizar documentación, versionar metadatos e inventariar IA','repository_organization.md'),
        ('quiero respoducible y para resultados todos los modelos de la ultima comapracaion menos l40 porque ese es de otro reposotprio y ahorita estamos manejando como champions ya depsues de toda al evidencia y demas 26 y 14','Seleccionar26/14 como champions y reproducir modelos propios excluyendoL40','current_champions_reproduction.md'),
        ('tambien actualiza el readme read me s para que reflehjen que ya estamos en esa stage con esos modelos','Actualizar navegación y estados a la etapa actual de champions','current_champions_reproduction.md'),
        ('tambien checa que en toda la documentacion ya quede 26 y 14 como champions y el chmpion pasado los de top20 y top 15 sean parte de la historia pero no confundan y quiero que los modelos de mi comparacion final cada uno tenga un read me completo de sus ventajas sus desventajas pero amas importante sus varaibles y en que punto y bajo que analisis surgieron','Documentar champions actuales, distinguir historial y explicar variables y origen de cada modelo','models/README.md'),
        ('incorpora las de los dos modelos champion a la comparacion exisitente','Consolidar26/14 y agregar sus59 predicciones a la comparación existente','models/README.md'),
        ('para 26 quiero una mejor pagina de documentacion quier especificos de los de 4 de climatico desde que modelo surgieron porque queson o minimo un linc a ct3 tambien las 7 varables del experto y como funcionan los usos de vecinos cunatos en que punto y tmabien los 3 variables de corrector expecificados','Ampliar documentación de26: origen C-T3, siete señales, vecinos, compuerta y correctorR3','models/Reference26/README.md'),
        ('quiero que ademas agregues esa metrica en los modelos donde los tengo disponibles ya sea en un  readme de comparacion global o dentro de las fichas especificas de los modelos','Incorporar el banco97/41 en comparación global y fichas disponibles','models/README.md'),
        ('okay tambien ahora para ams metodologicamente tengo duda en la parte de mis 4 variables climatica se especifica que no p test was done can yu mahe a hipotheisis testing for relevance de esas varaibels o dodne le daria mayor credidbilidad a mi modleo 26','Contrastar relevancia del núcleo C-T3 y distinguir asociación de aporte predictivo y credibilidad de26','models/Reference26/README.md'),
        ('realiza estos reportes como dices durante el modelado ya fueron explradas combinaciones existentes recura eso y presenta la manera en que cada factor fuede ser relevante o cumplor la funcion que se le dio','Recuperar ablaciones y evidencia existente por componente de26 sin duplicar modelado','models/Reference26/README.md'),
        ('las presentaciones de rewusltados si estan sobre las predicciones de 14 y 26 si no reggenra esos read me','Regenerar presentaciones vigentes de resultados y predicciones26/14','models/README.md'),
        ('porfavor checa que en todo el repositorio ya nos estemos refiriendo como champion a 26 y 14 nada ams','Reservar estado champion a26/14 y distinguir nombres heredados preservados','model_registry.md'),
        ('dame los rangos de las predicciones de 26 como platicamelos estadisticamente yu comparalos con la distribucion de los rendimeintos de las 138 parcelas por curiosisdad tmabiene stadisitcos desciptivos por estado y asi','Comparar distribución de59 predicciones26 con138 observaciones, global y por estado/municipio','models/Reference26/README.md'),
    ]
    messages.append(('realiza las 4 investigaciones y presenta resultados',
                     'Ejecutar auditoría de entrega, soporte59, cobertura de intervalos y sensibilidad completa de26 sin HHI; preservar champions26/14',
                     'models/Reference26/README.md'))
    for j,(message,purpose,evidence) in enumerate(messages,len(rows)+1):
        target=ROOT/'documentation/ai/prompts'/f'P{j:03d}_conversation.txt'
        target.write_text(message,encoding='utf-8')
        rows.append(dict(prompt_id=f'P{j:03d}',tool='Codex (asistente de IA generativa)',model='No registrado de forma verificable para este intercambio',
                         date='Fecha histórica no recuperada',purpose=purpose,transcription='Literal: mensaje del usuario visible en el contexto de conversación',
                         source='Conversación del proyecto; contexto previo no incluido en este extracto',prompt_file=target.relative_to(ROOT).as_posix(),sha256=sha(target),
                         related_document='documentation/'+evidence,execution_caveat='Consultar el contexto y los artefactos: este extracto no especifica por sí solo toda la receta.'))
    csv_write(ROOT/'documentation/ai/prompt_inventory.csv',list(rows[0]),rows)
    table='# Prompts recuperados: índice de originales\n\n'
    table+='Este índice contiene solicitudes, no un registro de ejecución. Herramienta receptora: Codex; versión histórica del modelo no verificada. Véase [alcance del inventario](../ai_usage.md).\n\n'
    table+='| ID | Propósito | Texto conservado | Evidencia relacionada |\n|---|---|---|---|\n'
    for row in rows:
        prompt=Path(row['prompt_file']).relative_to('documentation/ai').as_posix()
        evidence=Path(row['related_document']).relative_to('documentation').as_posix()
        table+=f"| {row['prompt_id']} | {row['purpose']} | [Literal]({prompt}) | [Documento](../{evidence}) |\n"
    (ROOT/'documentation/ai/README.md').write_text(table,encoding='utf-8')
    return len(rows)


def main():
    n=export_designs()
    export_splits()
    environment()
    count=prompts()
    inventories()
    print(json.dumps(dict(design_snapshots=n,prompts=count,trained_models=0,copied_datasets=0,predictions_generated=0)))


if __name__=='__main__':
    main()

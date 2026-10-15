"""Target-free follow-up: exact thermal/rain pairs, altitude and geographic support."""
from pathlib import Path
import sys,json,itertools,argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from pyproj import Geod
import plotly.graph_objects as go
from plotly.subplots import make_subplots
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from family_1.climate_signal_features import ID,MIN,MAX,paths,sha
from family_1.climate_signal_descriptive import geography

def exact_pairs(frame,column):
    return {tuple(sorted(pair)) for _,g in frame.groupby(column) for pair in itertools.combinations(g[ID],2)}

def markdown(frame):
    rows=[list(frame.columns),['---']*len(frame.columns)]+frame.astype(str).values.tolist()
    return '\n'.join('| '+' | '.join(row)+' |' for row in rows)

def interpretation(stats,correlations):
    c=correlations[correlations.level.str.startswith('53')].set_index(['temperature','predictor'])
    return (f"**Coinciden exactamente los grupos y los {stats['identical_pair_count']:,} pares**, tanto para Tmin como para Tmax y su combinación.\n\n"
        f"Los perfiles son locales: distancia mediana {stats['distance_median_km']:.2f} km y máxima {stats['distance_max_km']:.2f} km entre parcelas iguales. Sin embargo, {stats['profiles_crossing_municipalities']} perfiles cruzan municipios y {stats['profiles_crossing_states']} cruzan estados: los límites administrativos no definen la cuadrícula climática.\n\n"
        f"**La altitud segmenta parcialmente, pero no determina el perfil.** Las parcelas van de {stats['altitude_min_m']:.0f} a {stats['altitude_max_m']:.0f} m. {stats['profiles_crossing_100m_bands']} perfiles atraviesan bandas de 100 m; la diferencia máxima dentro del mismo perfil es {stats['largest_profile_altitude_range_m']:.0f} m. El {stats['altitude_between_profile_variance_fraction']:.1%} de la variación de altitud está entre perfiles y el resto dentro; es una descomposición descriptiva, no clasificación validada.\n\n"
        f"**Tmax presenta un gradiente altitudinal más claro:** entre 53 perfiles, correlación de Pearson con altitud {c.loc[('tmax_cycle_mean','elevation_m'),'pearson']:.2f}. Tmin tiene una correlación global pequeña ({c.loc[('tmin_cycle_mean','elevation_m'),'pearson']:.2f}), mientras sus correlaciones con longitud y latitud son {c.loc[('tmin_cycle_mean','longitude'),'pearson']:.2f} y {c.loc[('tmin_cycle_mean','latitude'),'pearson']:.2f}. Son asociaciones de las medias abril–octubre de 2025, no coeficientes físicos de enfriamiento.\n\n"
        "El gráfico por estado muestra Tmin más baja en Tlaxcala. Al separar estados, Tmin disminuye con altitud, especialmente en Tlaxcala (tabla 08); la asociación global mezcla diferencias regionales. Tmax disminuye con altitud en los tres estados. No se han confirmado clusters ni se ha establecido causalidad.\n\n")

def run(run_id):
    gout,gproc=paths('G','v1')
    out=ROOT/'outputs/data_audit/family_1/g_temperature_signal'/run_id
    if (out/'manifest.json').exists():raise FileExistsError('Complete run; choose a new run ID')
    out.mkdir(parents=True,exist_ok=True)
    for name in ['tables','figures','report']:(out/name).mkdir(exist_ok=True)
    inputs=[gout/'tables/06_profile_memberships.csv',gproc/'climate_candidates_197.parquet',ROOT/'data/processed/family_1/features/topography_basic_features.parquet']
    before={str(p.relative_to(ROOT)):sha(p) for p in inputs}
    frame=pd.read_parquet(inputs[1]);members=pd.read_csv(inputs[0])
    topo=pd.read_parquet(inputs[2]).rename(columns={'TOPO_BASIC_elevation_mean':'elevation_m','TOPO_BASIC_slope_mean':'slope_degrees'})
    geo=geography()
    q=frame[[ID]+MIN+MAX].merge(members,on=ID,validate='one_to_one').merge(topo[[ID,'elevation_m','slope_degrees']],on=ID,validate='one_to_one').merge(geo[[ID,'Estado','Municipio','longitude','latitude']],on=ID,validate='one_to_one')
    assert len(q)==197 and q[ID].is_unique and q.elevation_m.notna().all()
    q['tmin_cycle_mean']=q[MIN].mean(axis=1);q['tmax_cycle_mean']=q[MAX].mean(axis=1)
    q['tmean_cycle_mean']=(q.tmin_cycle_mean+q.tmax_cycle_mean)/2
    q['altitude_band_100m']=np.floor(q.elevation_m/100).astype(int)*100
    rain_pairs=exact_pairs(q,'rain');audit=[]
    for name in ['tmin','tmax','thermal','joint']:
        pairs=exact_pairs(q,name)
        audit.append(dict(definition=name,n_profiles=q[name].nunique(),identical_pairs=len(pairs),same_as_rain_pairs=pairs==rain_pairs,thermal_only_pairs=len(pairs-rain_pairs),rain_only_pairs=len(rain_pairs-pairs)))
    pd.DataFrame(audit).to_csv(out/'tables/01_exact_pair_equivalence.csv',index=False)
    cross=q.groupby(['rain','thermal']).size().rename('n_parcels').reset_index()
    cross.to_csv(out/'tables/02_profile_crosswalk.csv',index=False)
    assert cross.rain.is_unique and cross.thermal.is_unique
    q.to_csv(out/'tables/03_parcel_altitude_geography_temperature.csv',index=False)
    summary=q.groupby('thermal').agg(n_parcels=(ID,'size'),rain_profile=('rain','first'),elevation_min=('elevation_m','min'),elevation_median=('elevation_m','median'),elevation_max=('elevation_m','max'),elevation_mean=('elevation_m','mean'),elevation_sd=('elevation_m','std'),n_altitude_bands=('altitude_band_100m','nunique'),n_states=('Estado','nunique'),n_municipalities=('Municipio','nunique'),states=('Estado',lambda a:'; '.join(sorted(set(a)))),municipalities=('Municipio',lambda a:'; '.join(sorted(set(a)))),tmin=('tmin_cycle_mean','first'),tmax=('tmax_cycle_mean','first'),tmean=('tmean_cycle_mean','first'),longitude=('longitude','mean'),latitude=('latitude','mean')).reset_index()
    summary['elevation_range_m']=summary.elevation_max-summary.elevation_min
    summary.to_csv(out/'tables/04_thermal_profiles_altitude.csv',index=False)
    geod=Geod(ellps='WGS84');indexed=q.set_index(ID);pair_rows=[]
    for a,b in sorted(rain_pairs):
        x,y=indexed.loc[a],indexed.loc[b];_,_,dist=geod.inv(x.longitude,x.latitude,y.longitude,y.latitude)
        pair_rows.append(dict(ID_A=a,ID_B=b,thermal_profile=int(x.thermal),distance_km=dist/1000,altitude_difference_m=abs(x.elevation_m-y.elevation_m),same_municipality=x.Municipio==y.Municipio,same_state=x.Estado==y.Estado))
    pair_table=pd.DataFrame(pair_rows);pair_table.to_csv(out/'tables/05_identical_pairs_distance_altitude.csv',index=False)
    correlations=[]
    for level,z in [('197 parcels, repeated climate values',q),('53 equally weighted thermal profiles',summary.rename(columns={'elevation_mean':'elevation_m','tmin':'tmin_cycle_mean','tmax':'tmax_cycle_mean','tmean':'tmean_cycle_mean'}))]:
        for thermal in ['tmin_cycle_mean','tmax_cycle_mean','tmean_cycle_mean']:
            for predictor in ['elevation_m','longitude','latitude']:
                correlations.append(dict(level=level,temperature=thermal,predictor=predictor,n=len(z),pearson=z[thermal].corr(z[predictor]),spearman=z[thermal].corr(z[predictor],method='spearman')))
    correlations=pd.DataFrame(correlations);correlations.to_csv(out/'tables/06_descriptive_correlations.csv',index=False)
    regions=[]
    for field in ['Estado','Municipio','altitude_band_100m']:
        for name,z in q.groupby(field):
            regions.append(dict(segmentation=field,segment=name,n_parcels=len(z),n_thermal_profiles=z.thermal.nunique(),elevation_min=z.elevation_m.min(),elevation_max=z.elevation_m.max(),tmin_mean=z.tmin_cycle_mean.mean(),tmax_mean=z.tmax_cycle_mean.mean()))
    pd.DataFrame(regions).to_csv(out/'tables/07_geographic_altitude_segments.csv',index=False)
    within=[]
    for region,z in q.groupby('Estado'):
        for thermal in ['tmin_cycle_mean','tmax_cycle_mean']:
            within.append(dict(state=region,n_parcels=len(z),n_profiles=z.thermal.nunique(),temperature=thermal,elevation_pearson=z.elevation_m.corr(z[thermal]),elevation_spearman=z.elevation_m.corr(z[thermal],method='spearman')))
    pd.DataFrame(within).to_csv(out/'tables/08_within_state_correlations.csv',index=False)
    total=((q.elevation_m-q.elevation_m.mean())**2).sum()
    within_ss=((q.elevation_m-q.groupby('thermal').elevation_m.transform('mean'))**2).sum()
    stats=dict(n_parcels=len(q),n_profiles=len(summary),rain_thermal_exact_pairs_identical=exact_pairs(q,'thermal')==rain_pairs,identical_pair_count=len(pair_table),distance_median_km=pair_table.distance_km.median(),distance_max_km=pair_table.distance_km.max(),pairs_over_10_km=int(pair_table.distance_km.gt(10).sum()),altitude_min_m=q.elevation_m.min(),altitude_max_m=q.elevation_m.max(),pair_altitude_difference_median_m=pair_table.altitude_difference_m.median(),pair_altitude_difference_max_m=pair_table.altitude_difference_m.max(),pairs_altitude_difference_over_50m=int(pair_table.altitude_difference_m.gt(50).sum()),profiles_crossing_100m_bands=int(summary.n_altitude_bands.gt(1).sum()),profiles_crossing_municipalities=int(summary.n_municipalities.gt(1).sum()),profiles_crossing_states=int(summary.n_states.gt(1).sum()),altitude_between_profile_variance_fraction=float(1-within_ss/total),largest_profile_altitude_range_m=summary.elevation_range_m.max())
    fig,axes=plt.subplots(1,3,figsize=(17,5))
    for col,ax in zip(['elevation_m','tmin_cycle_mean','tmax_cycle_mean'],axes):
        sc=ax.scatter(q.longitude,q.latitude,c=q[col],cmap='viridis',s=26);fig.colorbar(sc,ax=ax,label='m' if col=='elevation_m' else '°C');ax.set(title=col,xlabel='Longitud',ylabel='Latitud')
    fig.tight_layout();fig.savefig(out/'figures/01_geography_altitude_temperature.png',dpi=170);plt.close(fig)
    ordered=summary.sort_values('elevation_median').reset_index(drop=True)
    fig,ax=plt.subplots(figsize=(12,13))
    for i,r in ordered.iterrows():
        ax.plot([r.elevation_min,r.elevation_max],[i,i],c='steelblue',lw=2)
        ax.scatter(r.elevation_median,i,s=15+3*r.n_parcels,c='darkorange')
    ax.set_yticks(range(len(ordered)),[f"P{int(r.thermal)} (n={int(r.n_parcels)})" for r in ordered.itertuples()]);ax.set(xlabel='Altitud media parcelaria (m); línea min–max del grupo',ylabel='Perfil térmico exacto',title='Un perfil climático puede abarcar distintas altitudes');ax.grid(axis='x',alpha=.2);fig.tight_layout();fig.savefig(out/'figures/02_altitude_range_by_profile.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(13,5))
    for col,ax in zip(['tmin_cycle_mean','tmax_cycle_mean'],axes):
        sns.scatterplot(data=q,x='elevation_m',y=col,hue='Estado',s=35,alpha=.7,ax=ax);ax.set(xlabel='Altitud media parcelaria (m)',ylabel='Media abril–octubre 2025 (°C)',title=col)
    fig.tight_layout();fig.savefig(out/'figures/03_altitude_temperature_by_state.png',dpi=170);plt.close(fig)
    fig=make_subplots(rows=1,cols=2,subplot_titles=['Ubicación de los perfiles exactos','Altitud y temperatura media del ciclo'])
    for profile,z in q.groupby('thermal'):
        custom=np.array(z[[ID,'Estado','Municipio','elevation_m','tmin_cycle_mean','tmax_cycle_mean','rain','thermal']].astype(str))
        color=f'hsl({(int(profile)*137.508)%360:.2f},65%,45%)'
        hover='ID %{customdata[0]}<br>%{customdata[1]} / %{customdata[2]}<br>Altitud %{customdata[3]} m<br>Tmin %{customdata[4]} °C; Tmax %{customdata[5]} °C<br>Perfil lluvia %{customdata[6]}; térmico %{customdata[7]}<extra></extra>'
        for col,x,y in [(1,z.longitude,z.latitude),(2,z.elevation_m,z.tmean_cycle_mean)]:
            fig.add_trace(go.Scatter(x=x,y=y,mode='markers',name=f'Perfil {profile} (n={len(z)})',legendgroup=str(profile),showlegend=col==1,marker=dict(color=color,size=8),customdata=custom,hovertemplate=hover),row=1,col=col)
    buttons=[dict(label='Todos los perfiles',method='update',args=[dict(visible=[True]*len(fig.data))])]
    for i,profile in enumerate(sorted(q.thermal.unique())):
        buttons.append(dict(label=f'Perfil {profile}',method='update',args=[dict(visible=[j//2==i for j in range(len(fig.data))])]))
    fig.update_layout(title='Perfiles térmicos exactos: ubicación y altitud — 197 parcelas, sin rendimiento',height=680,updatemenus=[dict(buttons=buttons,x=0,y=1.13)],legend=dict(groupclick='togglegroup',title='Clic: mostrar/ocultar perfil'),margin=dict(t=120))
    fig.update_xaxes(title_text='Longitud',row=1,col=1);fig.update_yaxes(title_text='Latitud',row=1,col=1);fig.update_xaxes(title_text='Altitud media parcelaria (m)',row=1,col=2);fig.update_yaxes(title_text='Tmean aproximada del ciclo (°C)',row=1,col=2)
    fig.write_html(out/'figures/04_interactive_profile_geography_altitude.html',include_plotlyjs=True)
    text='# Perfiles térmicos exactos, lluvia, altitud y geografía\n\n'
    text+='Se comparan los valores mensuales de abril–octubre de 2025. No se usa rendimiento, no se reentrena ningún modelo y no se modifica G/H v1.\n\n'
    text+='## Coincidencia exacta\n\n'+markdown(pd.DataFrame(audit))+'\n\n'
    text+='Los códigos numéricos de perfil de lluvia y temperatura pueden ser distintos: la equivalencia corresponde a las parcelas que agrupan, no al número asignado. Tabla 02 proporciona la correspondencia uno a uno.\n\n'
    text+='## Altitud y ubicación\n\n'+interpretation(stats,correlations)+'```json\n'+json.dumps(stats,ensure_ascii=False,indent=2)+'\n```\n\n'
    text+='Correlaciones descriptivas de temperatura media del ciclo con altitud y ubicación; las parcelas con clima repetido no son mediciones climáticas independientes. Se repite el cálculo dando el mismo peso a cada uno de los 53 perfiles:\n\n'+markdown(correlations.round(4))+'\n\n'
    text+='La tabla 08 separa estados para revisar si una asociación global mezcla regiones. Una correlación regional no identifica un efecto causal de altitud. Los intervalos de altitud de perfiles distintos se pueden superponer; no se supone que una banda altitudinal determine un perfil único. Las bandas de 100 m son descriptivas, con extremos [k,k+100), sin selección por rendimiento.\n\n'
    text+='La altitud es la media zonal del DEM INEGI CEM4 de cada parcela, en metros. La temperatura es de la cuadrícula CHIRTS-ERA5 de 0.05°, con ponderación por intersección ya auditada. Diferencias de altitud dentro de un perfil no generan nuevas observaciones térmicas en esta fuente.\n\n'
    text+='[Abrir gráfico interactivo](../figures/04_interactive_profile_geography_altitude.html): seleccionar un perfil en el desplegable para localizar todas sus parcelas y sus altitudes; también permite zoom y consulta de ID, municipio y temperaturas.\n\n'
    for p in sorted((out/'figures').glob('*.png')):text+=f'![{p.stem}](../figures/{p.name})\n\n'
    (out/'report/thermal_profile_geography.md').write_text(text,encoding='utf-8')
    for name,digest in before.items():assert sha(ROOT/name)==digest
    manifest=dict(status='complete',summary=stats,input_hashes=before,source_hash=sha(Path(__file__)),hidden_y_used=False,models_fitted=0,artifacts={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(stats,indent=2),flush=True)
    print(correlations.round(4).to_string(index=False),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='profile_geography_v1');args=parser.parse_args()
    if Path(args.run_id).name!=args.run_id or args.run_id in ['.','..']:parser.error('Simple run ID required')
    run(args.run_id)

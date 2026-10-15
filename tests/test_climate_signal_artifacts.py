"""Integration checks against actual frozen G/H predictions and fitted pipelines."""
from pathlib import Path
import json,sys,unittest
import joblib
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from family_1.climate_signal_features import ID,MASTER,TARGET,paths,climate_current,supervised_data,sha,verify_snapshot
from family_1.climate_signal_modeling import ALIASES,partition_signature
from family_1.rainfall_pcr import load_frozen_splits

class ClimateSignalArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gout,proc=paths('G','v1');cls.hout,_=paths('H','v1')
        frame=pd.read_parquet(proc/'climate_candidates_197.parquet')
        original,_=climate_current()
        cls.train=supervised_data(frame.merge(original,on=ID,validate='one_to_one'),pd.read_csv(MASTER))
        cls.pred={s:pd.read_parquet(out/'tables/31_oof_individual.parquet') for s,out in [('G',cls.gout),('H',cls.hout)]}

    def test_all_repetitions_are_same_138_labeled_parcels(self):
        expected=self.train.set_index(ID)[TARGET]
        for p in self.pred.values():
            for _,z in p.groupby(['protocol','experiment','repeat']):
                self.assertEqual(len(z),138);self.assertTrue(z[ID].is_unique)
                self.assertEqual(set(z[ID]),set(expected.index))
                np.testing.assert_array_equal(z.y_true.to_numpy(),expected.loc[z[ID]].to_numpy())

    def test_original_climate_current_random_predictions_exactly_reused(self):
        old=pd.read_parquet(ROOT/'outputs/modeling/family_1/source_contribution/predictions/source_oof_predictions.parquet')
        old=old[old.pipeline.eq('ENET_CLIMATE_ONLY')]
        new=self.pred['H'];new=new[new.protocol.eq('random')&new.experiment.eq('H8_CLIMATE_CURRENT_ORIGINAL')]
        keys=['repeat','fold',ID];cols=keys+['y_true','y_pred']
        pd.testing.assert_frame_equal(old[cols].sort_values(keys).reset_index(drop=True),new[cols].sort_values(keys).reset_index(drop=True),check_dtype=False)

    def test_thermal_h_aliases_equal_g_without_refitting(self):
        keys=['protocol','repeat','fold',ID];cols=keys+['y_true','y_pred']
        for g,h in ALIASES.items():
            a=self.pred['G'];a=a[a.experiment.eq(g)][cols].sort_values(keys).reset_index(drop=True)
            b=self.pred['H'];b=b[b.experiment.eq(h)][cols].sort_values(keys).reset_index(drop=True)
            pd.testing.assert_frame_equal(a,b)

    def test_saved_outer_and_inner_assignments_match_prior_folds(self):
        _,old,_=load_frozen_splits(self.train)
        new=pd.read_csv(self.hout/'splits/outer_and_inner_splits.csv')
        pd.testing.assert_frame_equal(old.reset_index(drop=True),new[old.columns].reset_index(drop=True),check_dtype=False)
        for r in new.itertuples():
            tr=set(json.loads(r.train_ID_POLIGONO));va=set(json.loads(r.validation_ID_POLIGONO))
            self.assertFalse(tr&va);self.assertEqual(tr|va,set(self.train[ID]))
            inner=json.loads(r.inner_validation_ID_POLIGONO)
            self.assertEqual(set(sum(inner,[])),tr);self.assertEqual(sum(map(len,inner)),len(tr))

    def test_saved_models_replay_predictions_and_training_only_scaling(self):
        split=pd.read_csv(self.hout/'splits/outer_and_inner_splits.csv')
        indexed=self.train.set_index(ID)
        for section,out in [('G',self.gout),('H',self.hout)]:
            registry=pd.read_csv(out/'tables/32_experiment_registry.csv')
            for protocol in ['random','climate_profile','municipality','spatial']:
                rows=registry[registry.protocol.eq(protocol)&registry['repeat'].eq(1)&registry.fold.eq(1)]
                s=split[split.protocol.eq(protocol)&split['repeat'].eq(1)&split.fold.eq(1)].iloc[0]
                tr=json.loads(s.train_ID_POLIGONO);va=json.loads(s.validation_ID_POLIGONO)
                for r in rows.itertuples():
                    if r.status.startswith('cached'):continue
                    cols=json.loads(r.columns)
                    model=joblib.load(out/'models'/f'{protocol}_01_01_{r.experiment}.joblib')
                    saved=self.pred[section];saved=saved[saved.protocol.eq(protocol)&saved['repeat'].eq(1)&saved.fold.eq(1)&saved.experiment.eq(r.experiment)].set_index(ID).loc[va]
                    np.testing.assert_allclose(model.predict(indexed.loc[va,cols]),saved.y_pred,rtol=1e-12,atol=1e-12)
                    if 'scaler' in model.named_steps:
                        scaler=model.named_steps['scaler']
                        self.assertEqual(int(scaler.n_samples_seen_),len(tr))
                        np.testing.assert_allclose(scaler.mean_,indexed.loc[tr,cols].mean().to_numpy(),rtol=1e-12,atol=1e-12)
                    else:
                        for _,block,features in model.named_steps['blocks'].transformers_:
                            if isinstance(block,str):continue
                            self.assertEqual(int(block.named_steps['scaler'].n_samples_seen_),len(tr))
                            np.testing.assert_allclose(block.named_steps['scaler'].mean_,indexed.loc[tr,features].mean(),rtol=1e-12,atol=1e-12)

    def test_joint_groups_really_equal_rain_partition(self):
        groups=pd.read_csv(self.hout/'splits/group_memberships.csv')
        self.assertEqual(partition_signature(groups.climate_profile),partition_signature(groups.joint_profile))
        definition=json.loads((self.hout/'splits/profile_protocol_definition.json').read_text(encoding='utf-8'))
        self.assertTrue(definition['joint_partition_equal_existing_rain_partition'])

    def test_incremental_deltas_use_exactly_paired_folds(self):
        f=pd.read_csv(self.hout/'tables/41_fold_metrics.csv')
        d=pd.read_csv(self.hout/'tables/51_paired_fold_deltas.csv')
        for row in d.itertuples():
            z=f[f.protocol.eq(row.protocol)&f['repeat'].eq(row.repeat)&f.fold.eq(row.fold)].set_index('experiment')
            self.assertAlmostEqual(row.delta_RMSE,z.loc[row.base,'RMSE']-z.loc[row.combined,'RMSE'],places=12)

    def test_descriptive_scores_have_no_targets_and_manifests_verify(self):
        for out in [self.gout,self.hout]:
            for file in (out/'tables').glob('23_*scores.parquet'):
                scores=pd.read_parquet(file)
                self.assertEqual(len(scores),197);self.assertTrue(scores[ID].is_unique)
                self.assertFalse(set(scores.columns)&{TARGET,'y_true','y_pred'})
            m=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(m['status'],'complete');self.assertFalse(m['hidden_y_used'])
            for file,digest in m['artifacts'].items():self.assertEqual(sha(ROOT/file),digest,file)
            for file,digest in m['source_hashes'].items():self.assertEqual(sha(ROOT/file),digest,file)
        verify_snapshot(self.gout)

if __name__=='__main__':unittest.main()

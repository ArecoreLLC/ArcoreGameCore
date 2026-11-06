import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from subject_taxonomy import candidate_profiles,compose_parts,load_catalog,resolve_part,validate_catalog


class SubjectTaxonomyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.catalog=load_catalog()

    def test_catalog_validates(self):
        self.assertEqual(validate_catalog(self.catalog),[])

    def test_subject_aliases_select_profiles(self):
        self.assertEqual(candidate_profiles('cartoon jumping spider',self.catalog)[0]['profile'],'profile.arachnid')
        self.assertEqual(candidate_profiles('small propeller airplane',self.catalog)[0]['profile'],'profile.aircraft')

    def test_profile_scope_resolves_ambiguous_language(self):
        self.assertEqual(resolve_part('head',self.catalog,'profile.arachnid')['part'],'part.cephalothorax')
        self.assertEqual(resolve_part('body',self.catalog,'profile.arachnid')['status'],'ambiguous')
        self.assertEqual(resolve_part('body',self.catalog,'profile.wheeled_vehicle')['part'],'part.chassis')

    def test_unknown_is_preserved(self):
        result=resolve_part('sparkle emitter',self.catalog,'profile.arachnid')
        self.assertEqual((result['status'],result['part']),('unknown','part.unknown'))

    def test_broken_reference_is_rejected(self):
        catalog=copy.deepcopy(self.catalog)
        catalog['profiles']['profile.arachnid']['parts'][0]['part']='part.missing'
        self.assertTrue(any('unknown part' in error for error in validate_catalog(catalog)))

    def test_bad_required_count_is_rejected(self):
        catalog=copy.deepcopy(self.catalog)
        catalog['profiles']['profile.fish']['parts'][0]['count']=[0,1]
        self.assertTrue(any('required count minimum' in error for error in validate_catalog(catalog)))

    def test_expanded_profile_families_are_available(self):
        expected={'profile.amphibian','profile.turtle','profile.dinosaur_biped','profile.gastropod',
                  'profile.cnidarian','profile.humanoid_robot','profile.mech','profile.garment',
                  'profile.bridge','profile.terrain','profile.construction_machine','profile.appliance',
                  'profile.bow_weapon','profile.musical_instrument'}
        self.assertTrue(expected.issubset(self.catalog['profiles']))
        self.assertGreaterEqual(len(self.catalog['profiles']),40)

    def test_traits_compose_without_overwriting_profile_counts(self):
        result=compose_parts(self.catalog,'profile.quadruped',['trait.winged','trait.horned'])
        self.assertEqual(result['parts']['part.leg'],[2,4])
        self.assertEqual(result['parts']['part.wing'],[0,1])
        self.assertEqual(result['parts']['part.horn'],[0,1])

    def test_unknown_trait_and_broken_topology_are_rejected(self):
        with self.assertRaises(KeyError):compose_parts(self.catalog,'profile.quadruped',['trait.imaginary'])
        catalog=copy.deepcopy(self.catalog)
        catalog['topology_templates']['topology.arachnid']['edges'][0][0]='part.missing'
        self.assertTrue(any('unknown edge part' in error for error in validate_catalog(catalog)))


if __name__=='__main__':unittest.main()

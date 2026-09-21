keywords: tests-page, campaign-catalog, operator-isolation, version-gaps, wrap-family, copy-parked, setup-popup
main_idea: Setup stays campaign + START. Add/edit/import tests live on the Tests page (Setup button -> popup). Enable writes this operator Version catalog only. Never merge another person. Same category on wrap.

Campaign `_manifest/test_catalog.yaml` `enabled_tests` wins over part yaml. A short catalog hides CPD/CIN even when `ate/config/parts/<key>.yaml` lists them. Customize must write this Version catalog (keep ORT/GBW keys) and must not write shared part yaml or Ariff/ChangThong folders.

Copy-from-part UI is parked. Wrap family is locked to the campaign family. Version gaps walk `#Test_Database/{Component}/{Part}/{Package}/{ThisOperator}/Version_*` plus part yaml / sheet_map ids that match the registry. Other operator folders are listed as skipped, not merged.

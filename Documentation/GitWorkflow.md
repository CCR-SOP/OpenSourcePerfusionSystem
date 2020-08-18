# Git Workflow for Liver Perfusion Project
----

Repository: https://github.com/NIH-CIT-OIR-SPIS/LiverPerfusion

## Folder Structure

Subfolders within the main folders (listed below) should be created to maintain a 
reasonable organization structure. For example, under the Models folder, each unique new model
should be placed under an appropriate subfolder (e.g. LiverCompression).

* Main Folders
	* Circuits - for schematics and printed circuit board layouts
	* Code - for programming code
	* Documentation - datasheets, specs, flowcharts, etc.
	* Models - for 3D CAD models
	
## Git Worflow Concepts
* The master branch should always be "deployable", meaning that all designs should be final, i.e. tested and in working order. 
* All work should be done in branches, never directly in master.
* To bring a branch into master, a GitHub Pull Request should be issued so the senior engineer can review before the merge takes place.
* The branch naming scheme wil use two main sub-branches names
  * Main sub-branch names:
    * feature - for adding new features/code/models/documentation
    * fixes - for bugfixes to code/models/documentation
	* Example branch creation: *git checkout -b feature/documentation_updates_for_workflow*
* Branches are normally branched from master, but it is acceptable to branch from a another branch in some situation
* Branch names should be descriptive, without being excessively long
* Work done in a branch should be specific to a single goal. Once completed, it should be merged back into master
* After a successful merge into master, a branch should be deleted (both locally and remotely)
* Commits should be done early and often
* Commits should contain a single concept
* Commits should have meaningful log messages which clearly describe the intend of the commit

## Tagging
* Tags will be used to denote deployed or fabricated products (e.g. code, models, circuits). Code which is installed on the main system for testing, but not accessible to end users will also be considered a fabricated product. 
* Deployed means the product was fabricated (e.g. a model was 3D printed)or installed (e.g. code) in the system for end-users
* Fabricated means a physical entity (e.g. 3D-printed part, circuit) was created, regardless of whether that specific fabrication is deployed
* If a fabricated product is deployed with no changes, then it will retain the same tag
* In git, tags are specific to a commit and the tag namespace exists over the full repository. In other words, care must be taken to distinguish tags for different products. So, for instance, use GlucoseAdapter_v1.0.0 or GA_v1.0.0 vs simply v1.0.0
* Fabricated parts should be tagged in their branch. If the fabricated part is deployed, that branch will be moved into master. If the fabricated part is not deployed, development can continue on that branch or the branch can be deleted.
* Annotated tags should be used as they allow a log message. The log message should contain any other usefull information such as the date of deployment, configuration information (e.g. if a Solidworks configuration as multiple configs, which config was fabricated)


## Version Numbering for Tagging
* Versioning will use a x.y.z format. X represent the major version, Y represents a minor version, Z represents a patch
* Major versions represent a significant change in the design, particularly when the change is not backwards compatible with previous versions
  * For example, 3D-printed part which has connections for tubing. If the new version requires larger tubing than the previous version, the major version should be udpated
  * There are no hard/fast rules, so use good judgement
* Minor version represent minor changes to the design, such as bug fixes or new features that don't break backwards compatibility.
* Patch versions represent very minor changes that do not impact functionality. Examples include fixing typos in a graphical user interface, deleting old comments in code, etc.
* If possible the version should be embedded in the fabricated product (e.g. added as comment in code or "About" box, "engraved" into 3D-printed part, etc.). This is not always possible, especially for physical parts. Good judgement should be used as to how a version number is added to a physical part.




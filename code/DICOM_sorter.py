import os, sys, time
import pydicom as dcm

#TO DO: comment

# TO DO: extend dict with other image types
dict_class_UID = {'1.2.840.10008.5.1.4.1.1.2': 'CT', '1.2.840.10008.5.1.4.1.1.481.1': 'RI', '1.2.840.10008.5.1.4.1.1.4': 'MR', '1.2.840.10008.5.1.4.1.1.128':'PE'}


def remove_RI_RT_files(PATH):
	"""
	remove_RI_RT_files Sorts the DICOM RT Image files (and associated registration files) into directory "RI"
					   and DICOM RT Treatment Record files into directory "RT". 
					   Note: This can be changed to delete the files entirely if not needed.

	:param PATH: Path to patient directory.
	"""

	# Counts for the number of each file type moved
	RI_count = 0
	RT_count = 0
	RE_count = 0
	
	file_list = [f for f in os.listdir(PATH) if os.path.isfile(os.path.join(PATH, f)) if 'RI' in f or 'RT' in f or 'RE' in f]

	# Create RT and RI directories if they don't exist
	RT_path = PATH + "RT"
	if not os.path.exists(RT_path):
		os.system("sudo mkdir " + RT_path)
		print("Created directory "+RT_path)

	RI_path = PATH + "RI"
	if not os.path.exists(RI_path):
		os.system("sudo mkdir " + RI_path)
		print("Created directory "+RI_path)
	
	# Go through each file in list and move into associated directory
	for file in file_list:
		if 'RT' in file:
			os.system("sudo mv " + PATH+file +" " + RT_path+"/"+file)
			RT_count += 1
		
		elif 'RI' in file:
			os.system("sudo mv " + PATH+file +" " + RI_path+"/"+file)
			RI_count += 1
		
		elif 'RE' in file:
			# Check if registration file is referencing an "RI" image file
			RE_class = dcm.read_file(PATH+file).ReferencedSeriesSequence[0].ReferencedInstanceSequence[0].ReferencedSOPClassUID
			if dict_class_UID[RE_class] == 'RI':
				os.system("sudo mv " + PATH+file +" " + RI_path+"/"+file)
				RE_count += 1
	print("--------------------------------------------------------------------------------")
	print("Files moved: ", RT_count, " RT, ", RI_count, " RI, ",RE_count, " RE")
	print("--------------------------------------------------------------------------------")
				
def remove_non_CT_image_files(PATH):
	"""
	remove_non_CT_image_files Sorts the DICOM MRI and PET Image files into directories "MR" and "PE".
							  The scans are not sorted within these folders as they aren't needed for this project.
					   		  Note: This can be changed to delete the files entirely if not needed.
					   		  Note: Can add other image types in the same manner if they arise.

	:param PATH: Path to patient directory.
	"""

	file_list_PE = [f for f in os.listdir(PATH) if os.path.isfile(os.path.join(PATH, f)) if 'PE' in f]
	file_list_MR = [f for f in os.listdir(PATH) if os.path.isfile(os.path.join(PATH, f)) if 'MR' in f]
	
	num_PE = len(file_list_PE)
	num_MR = len(file_list_MR)

	# If PET or MRI files exist, create and move into associated directories
	if num_PE > 0:
		PE_path = PATH + "PE"
		if not os.path.exists(PE_path):
			os.system("sudo mkdir " + PE_path)
			print("Created directory "+PE_path)
		for file in file_list_PE:
			os.system("sudo mv "+PATH+file+" "+PE_path+"/"+file)
	
	if num_MR > 0:
		MR_path = PATH + "MR"
		if not os.path.exists(MR_path):
			os.system("sudo mkdir " + MR_path)
			print("Created directory "+MR_path)
		for file in file_list_MR:
			os.system("sudo mv "+PATH+file+" "+MR_path+"/"+file)

	if num_PE + num_MR > 0:
		print("--------------------------------------------------------------------------------")
		print("Files moved: ",num_PE, " PET, ", num_MR, " MR")
		print("--------------------------------------------------------------------------------")

			

def sort_image_files_by_RS(PATH):
	"""
	sort_image_files_by_RS Sorts the CT slice files (and associated registration files), RT Structure Set files
						   and RT Dose files into directories corresponding to each image sequence. Sorting is
						   done based on the RS file, which is associated to RD and RE files using the 
						   FrameOfReferenceUID tag, and to the CT files using the ReferencedSOPInstanceUID tag.
						   Since the CT files are named after this UID tag, this sorting method does not require 
						   opening/reading the CT files.

	:param PATH: Path to patient directory.
	"""
	# Dictionary containing the frame of reference UIDs and the associated file path they belong to
	uid_dict = {}
	
	# List of each file type to be moved
	list_RE = []
	list_RS = []
	list_RD = []
	other = [] # Catch-all if a new file type appears

	# Counts of each file type to be moved
	CT_count = 0
	RE_count = 0
	RS_count = 0
	RD_count = 0
	
	# Get all non-CT files
	file_list = [f for f in os.listdir(PATH) if os.path.isfile(os.path.join(PATH, f)) if 'CT' not in f]
	
	# Creat sub-list of file types
	for file in file_list:
		if 'RE' in file:
			list_RE.append(file)
		elif 'RS' in file:
			 list_RS.append(file)
		elif 'RD' in file:
			list_RD.append(file)
		else:
			other.append(file)
			
	# For each RS file, create directory and move associated CT slices
	for file in list_RS:
		d = dcm.read_file(PATH+file)
		
		new_path = PATH + d.StructureSetDate + "_" +  d.StructureSetLabel # New directory path: Date_Label

		# Create new directory if not exists
		if not os.path.exists(new_path):
			os.system("sudo mkdir " + new_path)
			print("Created directory "+new_path)
	
		# Move current RS file into new directory
		os.system("sudo mv " + PATH+file +" " + new_path+"/"+file)
		RS_count += 1

		# Save the frame of reference UID into dictionary with associated new directory path
		# Note: the RS, RD and RE files have the same FrameOfReferenceUID, so this dict is used to move RD & RE later
		frame_of_reference_uid = d.ReferencedFrameOfReferenceSequence[0].FrameOfReferenceUID
		uid_dict.update({frame_of_reference_uid: new_path}) 

		# Do not gather CT files for "PlanAdapt" structure sets, as these are tests done on the planning CT which will be put into its own folder
		# Note: this code keeps the PlanAdapt directory, but it could be deleted as it won't be useful.
		if "PlanAdapt" not in d.StructureSetLabel:
			# For each image slice referenced in RS file, move the correspondint CT file into the new directory
			# Note: the CT files are automatically named as "CT.ReferencedSOPInstanceUID.dcm"
			for img in d.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence:
				uid = img.ReferencedSOPInstanceUID 
				os.system("sudo mv " + PATH+"CT."+uid+".dcm" +" " + new_path+"/"+"CT."+uid+".dcm")
				CT_count += 1

	
	# Organize the registration (RE) files into the appropriate directories based on FrameOfReferenceUID
	for file in list_RE:
		d = dcm.read_file(PATH+file)
		try:
			frame_of_reference_uid = d.RegistrationSequence[1].FrameOfReferenceUID
		except:
			frame_of_reference_uid = d.FrameOfReferenceUID

		# Catch exception if RE file doesn't belong to any of the images downloaded
		try:
			os.system("sudo mv " + PATH+file +" " + uid_dict[frame_of_reference_uid]+"/"+file)
			RE_count += 1
		except:
			print("could not move file ", file, " with frame of ref uid ",frame_of_reference_uid)


	# Organize the dose (RD) files into the appropriate directories based on FrameOfReferenceUID
	for file in list_RD:
		d = dcm.read_file(PATH+file)
		frame_of_reference_uid = d.FrameOfReferenceUID

		try:
			os.system("sudo mv " + PATH+file +" " + uid_dict[frame_of_reference_uid]+"/"+file)
			RD_count += 1
		except:
			print("could not move file ", file, " with frame of ref uid ",frame_of_reference_uid)

	
	# Display other file types caught
	if len(other) != 0:
		print("Other files not moved:")
		for file in other:
			print(file)
	
	print("--------------------------------------------------------------------------------")
	print("Files moved: ",CT_count, " CT, ", RS_count, " RS, ", RE_count, " RE, ",RD_count, " RD")
	print("--------------------------------------------------------------------------------")



def remove_unneeded_RE_files(PATH):
	"""
	remove_unneeded_RE_files Deletes remaining registration files associated to an image sequence 
							 that was not downloaded.

	:param PATH: Path to patient directory.
	"""
	# TO DO: move into MR and PE files if exist
	file_list = [f for f in os.listdir(PATH) if os.path.isfile(os.path.join(PATH, f)) and 'RE' in f]
	for file in file_list:
		d = dcm.read_file(PATH+file)
		class_UID = d.RegistrationSequence[1].ReferencedImageSequence[0].ReferencedSOPClassUID

		ref_image_class = dict_class_UID[class_UID] 

		if ref_image_class != 'CT' and os.path.exists(PATH+ref_image_class):
			print("Moving "+ref_image_class+" registration file.")
			os.system("sudo mv " + PATH+file +" " + PATH+ref_image_class+"/"+file)

		else:
			print("Removing "+ref_image_class+" registration file.")
			os.system("sudo rm " + PATH+file)




def organize_multiple_patients(list_patients, PATH):
	"""
	organize_multiple_patients calls each of the sorting functions for each patient to be sorted.

	:param list_patients: list of patient directories to be sorted.
	:param PATH: main path to patient directories.
	"""

	for patient in list_patients:
		print("================================================================================")
		print("Patient ", patient)
		print("--------------------------------------------------------------------------------")
		patient_path = PATH + str(patient) + "/"

		# Call each sorting function
		remove_RI_RT_files(patient_path)
		remove_non_CT_image_files(patient_path)
		sort_image_files_by_RS(patient_path)
		remove_unneeded_RE_files(patient_path)

		# Print files that were not sorted
		print("Files Remaining:")
		print([f for f in os.listdir(patient_path) if os.path.isfile(os.path.join(patient_path, f))])
	  


if __name__ == "__main__":
	
	PATH = '/mnt/iDriveShare/Kayla/CBCT_images/kayla_extracted/' # Path to patient directories
	list_patients_to_sort = [] # Patient directories to sort

	# Check if command line arguments correspond to existing patient directories
	for patient in sys.argv[1:]:
		if os.path.exists(PATH+patient):
			list_patients_to_sort.append(patient)
		else:	
			print("Patient directory "+ PATH+patient + " does not exist.")
	

	organize_multiple_patients(list_patients_to_sort, PATH)    


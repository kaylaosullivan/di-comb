import os, sys, time
import pydicom as dcm

#TO DO: comment

# TO DO: extend dict with other iage types
dict_class_UID = {'1.2.840.10008.5.1.4.1.1.2': 'CT', '1.2.840.10008.5.1.4.1.1.481.1': 'RI', '1.2.840.10008.5.1.4.1.1.4': 'MR', '1.2.840.10008.5.1.4.1.1.128':'PET'}


def remove_RI_RT_files(PATH):
	"""
	remove_RI_RT_files Sorts the DICOM RT Image files (and associated registration files) into directory "RI"
					   and DICOM RT Treatment Record files into directory "RT". 

	:param PATH: Path to patient directory.
	"""

	RI_count = 0
	RT_count = 0
	RE_count = 0
	
	file_list = [f for f in os.listdir(PATH) if os.path.isfile(os.path.join(PATH, f))]
	
	RT_path = PATH + "RT"
	if not os.path.exists(RT_path):
		os.system("sudo mkdir " + RT_path)
		print("Created directory "+RT_path)

	RI_path = PATH + "RI"
	if not os.path.exists(RI_path):
		os.system("sudo mkdir " + RI_path)
		print("Created directory "+RI_path)
	
	for file in file_list:
		if 'RT' in file:
			os.system("sudo mv " + PATH+file +" " + RT_path+"/"+file)
			RT_count += 1
		elif 'RI' in file:
			os.system("sudo mv " + PATH+file +" " + RI_path+"/"+file)
			RI_count += 1
		elif 'RE' in file:
			RE_class = dcm.read_file(PATH+file).ReferencedSeriesSequence[0].ReferencedInstanceSequence[0].ReferencedSOPClassUID
			if dict_class_UID[RE_class] == 'RI':
				os.system("sudo mv " + PATH+file +" " + RI_path+"/"+file)
				RE_count += 1
	print("--------------------------------------------------------------------------------")
	print("Files moved: ", RT_count, " RT, ", RI_count, " RI, ",RE_count, " RE")
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

	uid_dict = {}
	
	list_RE = []
	list_RS = []
	list_RD = []
	other = []
	CT_count = 0
	RE_count = 0
	RS_count = 0
	RD_count = 0
	
	
	file_list = [f for f in os.listdir(PATH) if os.path.isfile(os.path.join(PATH, f))]
	
	for file in file_list:
		if 'RE' in file:
			list_RE.append(file)
		elif 'RS' in file:
			 list_RS.append(file)
		elif 'RD' in file:
			list_RD.append(file)
		elif 'CT' not in file:
			other.append(file)
			
	for file in list_RS:
		if 'RS' in file:
			d = dcm.read_file(PATH+file)
			
			new_path = PATH + d.StructureSetDate + "_" +  d.StructureSetLabel

			if not os.path.exists(new_path):
				os.system("sudo mkdir " + new_path)
				print("Created directory "+new_path)
		
			os.system("sudo mv " + PATH+file +" " + new_path+"/"+file)
			RS_count += 1
	
			frame_of_reference_uid = d.ReferencedFrameOfReferenceSequence[0].FrameOfReferenceUID
			uid_dict.update({frame_of_reference_uid: new_path})

		
			
			for img in d.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence:
				uid = img.ReferencedSOPInstanceUID 
				os.system("sudo mv " + PATH+"CT."+uid+".dcm" +" " + new_path+"/"+"CT."+uid+".dcm")
				CT_count += 1

	
	for file in list_RE:
		d = dcm.read_file(PATH+file)
		try:
			frame_of_reference_uid = d.RegistrationSequence[1].FrameOfReferenceUID
		except:
			print("HERE")
			frame_of_reference_uid = d.FrameOfReferenceUID

		try:
			os.system("sudo mv " + PATH+file +" " + uid_dict[frame_of_reference_uid]+"/"+file)
			RE_count += 1
		except:
			print("could not move file ", file, " with frame of ref uid ",frame_of_reference_uid)


	for file in list_RD:
		d = dcm.read_file(PATH+file)
		frame_of_reference_uid = d.FrameOfReferenceUID

		try:
			os.system("sudo mv " + PATH+file +" " + uid_dict[frame_of_reference_uid]+"/"+file)
			RD_count += 1
		except:
			print("could not move file ", file, " with frame of ref uid ",frame_of_reference_uid)

	
	if len(other) != 0:
		print("Other files not moved")
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

	file_list = [f for f in os.listdir(PATH) if os.path.isfile(os.path.join(PATH, f)) and 'RE' in f]
	for file in file_list:
		d = dcm.read_file(PATH+file)
		class_UID = d.RegistrationSequence[1].ReferencedImageSequence[0].ReferencedSOPClassUID
		if dict_class_UID[class_UID] != 'CT':
			print("Removing "+dict_class_UID[class_UID]+" registration file.")
#             print("sudo rm " + PATH+file)
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


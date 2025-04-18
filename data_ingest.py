from helpers import download_data, header_correction

prescriptions_url = "https://www.opendatani.gov.uk/@business-services-organisation/gp-prescribing-data"
practice_patient_count_url = "https://www.opendatani.gov.uk/@business-services-organisation/gp-practice-list-sizes"
practice_name_url = "https://www.opendatani.gov.uk/@business-services-organisation/gp-practice-list-sizes"
path_prescriptions = './data/prescribing_data'
path_practice_details = './data/practice_name'

download_data(prescriptions_url, 'csv', 'prescribing_data')
header_correction(path_prescriptions)

if __name__ == '__main__':
    header_correction(path_prescriptions)
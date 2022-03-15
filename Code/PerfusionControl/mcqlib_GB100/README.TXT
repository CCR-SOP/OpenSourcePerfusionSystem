**********************************
******* MCQ PYTHON LIBRARY *******
**********************************


## INSTALLATION
1. Install Python 3.7 or higher
  verify correct installation with command:
  > python --version
  or
  > python3.x --version 
  (if you have multiple python versions installed)

2. Verify pip3 is installed (package manager)  
  > pip3 --version

  (Should be installed together with Python. If not, search on google how to install pip3)

3. Install package minimalmodbus (modbus wrapper, required to communicate with the instrument)
  > pip3 install minimalmodbus

4. Configure correct serial connection settings in file ./mcqlib/config.ini
  - COM Port
  - Baud Rate

5. Open CMD (terminal), navigate to root folder (where read_sample1.py is located) and run command:
  > python read_sample1.py

  Wait for the program to end, the terminal should output a list of values, eg:

  # python read_sample1.py                             
    Script Start                                       
    fw ver 0109                                        
    hw ver 0100                                        
    Reading Channels Values...                         
    Channel 1 - Gas Id: 2, Gas: Nitrogen, K-Factor: 1.0
    Channel 2 - Gas Id: 3, Gas: Oxygen, K-Factor: 0.872
    Channel 3 - Gas Id: 7, Gas: Argon, K-Factor: 1.1   
    Script End
  

## REQUIRED LIBRARIES:
  - minimalmodbus==1.0.2
  - pyserial==3.4
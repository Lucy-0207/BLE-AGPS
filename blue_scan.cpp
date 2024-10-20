#define _CRT_SECURE_NO_WARNINGS
#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include <iomanip>
#include <windows.h>
#include <bluetoothapis.h>
#include <winsock.h>
#include <ws2bth.h>
#pragma comment(lib, "wsock32.lib")
#pragma comment(lib, "bthprops.lib")
#pragma comment(lib, "ws2_32.lib")

using namespace std;

string wstring2string(const wstring& ws)
{
    string curLocale = setlocale(LC_ALL, NULL);
    setlocale(LC_ALL, "chs");
    const wchar_t* _Source = ws.c_str();
    size_t _Dsize = 2 * ws.size() + 1;
    char* _Dest = new char[_Dsize];
    memset(_Dest, 0, _Dsize);
    wcstombs(_Dest, _Source, _Dsize);
    string result = _Dest;
    delete[] _Dest;
    setlocale(LC_ALL, curLocale.c_str());
    return result;
}

string getMAC(BLUETOOTH_ADDRESS Daddress)
{
    ostringstream oss;
    oss << hex << setfill('0') << uppercase;
    for (int i = 5; i >= 0; --i) {
        oss << setw(2) << static_cast<int>(Daddress.rgBytes[i]);
        if (i > 0) {
            oss << ":";
        }
    }
    return oss.str();
}

// 修改后的 scanDevices 函数，返回字符串
extern "C" __declspec(dllexport) const char* scanDevices()
{
    HBLUETOOTH_RADIO_FIND hbf = NULL;
    HANDLE hbr = NULL;
    HBLUETOOTH_DEVICE_FIND hbdf = NULL;
    BLUETOOTH_FIND_RADIO_PARAMS btfrp = { sizeof(BLUETOOTH_FIND_RADIO_PARAMS) };
    BLUETOOTH_RADIO_INFO bri = { sizeof(BLUETOOTH_RADIO_INFO) };
    BLUETOOTH_DEVICE_SEARCH_PARAMS btsp = { sizeof(BLUETOOTH_DEVICE_SEARCH_PARAMS) };
    BLUETOOTH_DEVICE_INFO btdi = { sizeof(BLUETOOTH_DEVICE_INFO) };
    hbf = BluetoothFindFirstRadio(&btfrp, &hbr);

    std::ostringstream oss;

    bool brfind = hbf != NULL;
    while (brfind)
    {
        if (BluetoothGetRadioInfo(hbr, &bri) == ERROR_SUCCESS)
        {
            oss << "[Local Device Name]: " << wstring2string(bri.szName);
            oss << " [Local Device Address]: " << getMAC(bri.address) << "\n";

            btsp.hRadio = hbr;
            btsp.fReturnAuthenticated = TRUE;
            btsp.fReturnConnected = FALSE;
            btsp.fReturnRemembered = TRUE;
            btsp.fReturnUnknown = TRUE;
            btsp.fIssueInquiry = TRUE;
            btsp.cTimeoutMultiplier = 30;
            hbdf = BluetoothFindFirstDevice(&btsp, &btdi);
            bool bfind = hbdf != NULL;

            while (bfind)
            {
                oss << "[Name]: " << wstring2string(btdi.szName);
                oss << " [Address]: " << getMAC(btdi.Address) << "\n";
                bfind = BluetoothFindNextDevice(hbdf, &btdi);
            }
            BluetoothFindDeviceClose(hbdf);
        }
        CloseHandle(hbr);
        brfind = BluetoothFindNextRadio(hbf, &hbr);
    }

    static std::string result = oss.str();
    return result.c_str();
}

void main()
{
    const char* devices = scanDevices();
    cout << devices;
}

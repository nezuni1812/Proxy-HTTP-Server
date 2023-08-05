#include <iostream>
#include <fstream>
#include <string>
#include <vector>

using namespace std;

//Lấy danh dách những trang phép được truy cập
vector<string> WhiteList();
//Kiểm tra xem trang web đang truy cập có nằm trong White list hay không
bool isWhiteList(vector<string> Wlist);


#include <iostream>
 
using namespace std;
 
class Mathematics {
  int x, y;
 
public:
  void input() {
    cout << "Input an integer\n";
    cin >> x;
    cout << "input the other integer\n";
    cin >> y;
  }
 
  void add() {
    cout << "Result = " << x + y;
  }
 
};
 
int main()
{
   Mathematics m; // Creating object of class
 
   m.input();
   m.add();
 
   return 0;
}

class HelloWorld{
  public static void main(String[] args){
    System.out.println("hello");
    int i = 1;
    int j = i + 2;
    System.out.println(j);
    System.out.println(3+4);

    for(int l = 0; l < 2; l++){
      System.out.println("progress");
    }
    int s = 0;
    for(int l = 1; l < 5; l++){
      s += l;
    }
    System.out.println(s);
    show();
    int c = constant();
    System.out.println(c);

    int r = identity(12345);
    System.out.println(r);

    System.out.println(add(1,30));

    System.out.println(fibonacci(15));
  }

  public static void show(){
    System.out.println("show string");
  }

  public static int constant(){
    return 1234;
  }

  public static int identity(int arg){
    return arg;
  }

  public static int add(int x, int y){
    return x + y;
  }

  public static int fibonacci(int n){
    if(n == 0){
      return 1;
    }else if(n == 1){
      return 1;
    }else{
      return fibonacci(n-1) + fibonacci(n-2);
    }
  }

}

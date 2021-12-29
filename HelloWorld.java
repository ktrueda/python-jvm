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
  }

  public static void show(){
    System.out.println("show string");
  }
}

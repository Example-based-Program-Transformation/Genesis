package com.basic.app;

/**
 * Hello world!
 *
 */
public class App
{

    App a = null;

    public String foo() {
        return Integer.toString(a.bar());
    }

    public int bar() {
        return 1;
    }

    public static void main( String[] args )
    {
        System.out.println( "Hello World!" );
    }
}

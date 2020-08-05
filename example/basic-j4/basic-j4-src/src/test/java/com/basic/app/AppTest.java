package com.basic.app;

import static org.junit.Assert.*;

import org.junit.Test;

public class AppTest {

	@Test
	public void testPass() {
		assertTrue(true);
	}

	@Test
	public void testBar() {
		App a = new App();
		assertTrue(a.bar() == 1);
	}

	@Test
	public void testFoo() {
		App a = new App();
		assertTrue(a.foo() == "");
	}
}

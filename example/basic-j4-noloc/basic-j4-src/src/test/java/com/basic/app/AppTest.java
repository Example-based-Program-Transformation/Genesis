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
		// Make localization difficult
		try {
			App a = new App();
			assertTrue(a.foo() == "");
		} catch (NullPointerException e) {
			// Oh no, that shouldn't have happened! Let's totally
			// destroy all the mildly useful information.
			assertTrue(false);
		}
	}
}

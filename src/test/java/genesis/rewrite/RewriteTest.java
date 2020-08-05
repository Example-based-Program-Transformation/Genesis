// Copyright (C) 2016 Fan Long, Peter Amidon, Martin Rianrd and MIT CSAIL 
// Genesis (A successor of Prophet for Java Programs)
// 
// This file is part of Genesis.
// 
// Genesis is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 2 of the License, or
// (at your option) any later version.
// 
// Genesis is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// 
// You should have received a copy of the GNU General Public License
// along with Genesis.  If not, see <http://www.gnu.org/licenses/>.
package genesis.rewrite;

import java.io.File;
import java.io.IOException;
import java.net.URL;
import java.nio.file.Files;
import java.nio.file.Paths;

import org.junit.Test;

import genesis.TestSnippetParser;
import genesis.node.MyCtNode;
import junit.framework.TestCase;

public class RewriteTest extends TestCase {
	
	@Test
	public void test() {
		URL folderURL = getClass().getResource("/rewrite/");
		assertNotNull("Test file not found!", folderURL);
		String[] cases =
			{"basic", "removevardecl", "commutativity", "literal"};
		String folder = folderURL.getPath();
		for (String casestr : cases) {
			System.out.println("Case: " + casestr);
			File beforef = new File(folder + "/" + casestr + "/before.jar");
			File afterf = new File(folder + "/" + casestr + "/after.jar");
			assertTrue("Case tarballs are missing!", beforef.exists() && afterf.exists());
			File expbeforef = new File(folder + "/" + casestr + "/expbefore.txt");
			File expafterf = new File(folder + "/" + casestr + "/expafter.txt");
			String expbefore = null;
			String expafter = null;
			if (expbeforef.exists()) {
				try {
					expbefore = new String(Files.readAllBytes(Paths.get(expbeforef.getPath())));
					expafter = new String(Files.readAllBytes(Paths.get(expafterf.getPath())));
				}
				catch (IOException e) {
					e.printStackTrace();
					fail("Failed to read exp java program.");
				}
			}
			
			TestSnippetParser p1 = new TestSnippetParser(beforef.getPath());
			TestSnippetParser p2 = new TestSnippetParser(afterf.getPath());
			
			MyCtNode beforeN = p1.getRootPackage();
			MyCtNode afterN = p2.getRootPackage();
			assertNotNull("Failed to parse before tree", beforeN);
			assertNotNull("Failed to parse after tree", afterN);
			RewritePassManager m = new RewritePassManager();
			m.addPass(new VarDeclEliminationPass());
			m.addPass(new CommutativityRewritePass());
			m.addPass(new LiteralRewritePass());
			m.addPass(new CodePairRewriteWrapperPass(new CodeStyleNormalizationPass()));
			m.run(beforeN, afterN);
			if (expbefore == null) {
				m.writeToFile("/tmp/" + casestr + "-expbefore.java", "/tmp/" + casestr + "-expafter.java");
				System.out.println("Output wrote to /tmp directory!");
			}
			else {
				String beforeStr = m.getBeforeCodeString();
				String afterStr = m.getAfterCodeString();
				assertTrue("Does not produce expected before.java", expbefore.equals(beforeStr));
				assertTrue("Does not produce expected after.java", expafter.equals(afterStr));
				System.out.println("OK");
			}
		}
	}
}

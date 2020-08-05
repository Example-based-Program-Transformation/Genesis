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
package genesis.generator;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.URL;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.TreeMap;

import org.junit.Test;

import genesis.SnippetPairParser;
import genesis.node.MyCtNode;
import genesis.schema.VarTypeContext;
import junit.framework.TestCase;
import spoon.reflect.factory.Factory;
import spoon.reflect.reference.CtReference;
import spoon.support.reflect.reference.CtExecutableReferenceImpl;
import spoon.support.reflect.reference.CtFieldReferenceImpl;

public class VarGeneratorTest extends TestCase {

	@SuppressWarnings("rawtypes")
	public void testGenerator(String d, String[] cases, Class<? extends VarGenerator> genClass) {
		URL folderURL = getClass().getResource("/generator/" + d + "/");
		assertNotNull("Test file not found!", folderURL);

		String folder = folderURL.getPath();
		System.out.println(d + " Generator unit test:");
		int passedCnt = 0;
		for (String casestr : cases) {
			File onecase = new File(folder + "/" + casestr);
			assertTrue("Unknown structure in resource /generator/" + d + "/", onecase.isDirectory());
			File[] files = onecase.listFiles();
			TreeMap<Integer, File> befores = new TreeMap<Integer, File>();
			TreeMap<Integer, File> afters = new TreeMap<Integer, File>();
			TreeMap<Integer, String> expstr = new TreeMap<Integer, String>();
			File exp = null;
			for (File f : files) {
				String fname = f.getName();
				if (fname.equals("exp.po"))
					exp = f;
				else if (fname.startsWith("before")) {
					int idx = fname.indexOf(".");
					assertTrue("Wrong file name patten " + fname, idx != -1);
					befores.put(Integer.parseInt(fname.substring(6, idx)), f);
				}
				else if (fname.startsWith("after")) {
					int idx = fname.indexOf(".");
					assertTrue("Wrong file name pattern " + fname, idx != -1);
					afters.put(Integer.parseInt(fname.substring(5, idx)), f);
				}
				else if (fname.startsWith("expstr")) {
					int idx = fname.indexOf(".");
					List<String> l = null;
					try {
						l = Files.readAllLines(Paths.get(f.getPath()));
					}
					catch (IOException e) {
						e.printStackTrace();
						fail("unable to read the file " + fname);
					}
					assertTrue("Unknown format in " + fname, l.size() > 0);
					expstr.put(Integer.parseInt(fname.substring(6, idx)), l.get(0));
					assertTrue("Wrong file name pattern " + fname, idx != -1);
				}
				else
					fail("Wrong file name pattern " + fname);
			}
			if (befores.size() != afters.size())
				fail("before/after pairs do not match!");

			ArrayList<MyCtNode> beforeList, treeList;
			ArrayList<Factory> facs;
			beforeList = new ArrayList<MyCtNode>();
			facs = new ArrayList<Factory>();
			treeList = new ArrayList<MyCtNode>();

			for (Integer cid : befores.keySet()) {
				assertTrue("before/after pairs do not match!", afters.containsKey(cid));
				SnippetPairParser parser = new SnippetPairParser(befores.get(cid).getPath(), afters.get(cid).getPath());
				MyCtNode before = parser.getOriTree1();
				MyCtNode tree = parser.getTree2();
				if (tree == null)
					fail("Cannot traverse down to the desired level!");
				beforeList.add(before);
				facs.add(parser.getTree1Factory());
				treeList.add(tree);
			}

			// Generate the context in a cheezy way
			ArrayList<VarTypeContext> contexts = new ArrayList<VarTypeContext>();
			for (int i = 0; i < treeList.size(); i++) {
				MyCtNode n = treeList.get(i);
				VarTypeContext tctxt = new VarTypeContext();
				if (n.isEleClass(CtExecutableReferenceImpl.class) ||
						n.isEleClass(CtFieldReferenceImpl.class)) {
					CtReference ref = (CtReference) n.getRawObject();
					if (ref instanceof CtExecutableReferenceImpl)
						tctxt.targetType = ((CtExecutableReferenceImpl) ref).getDeclaringType();
					else if (ref instanceof CtFieldReferenceImpl)
						tctxt.targetType = ((CtFieldReferenceImpl) ref).getDeclaringType();
				}
				contexts.add(tctxt);
			}

			System.out.println("\nCase " + casestr + ":");
			VarGenerator generator = null;
			if (genClass == EnumerateGenerator.class) {
				generator = EnumerateGenerator.createGenerator(treeList, beforeList, contexts);
			}
			else if (genClass == ReferenceGenerator.class) {
				generator = ReferenceGenerator.createGenerator(treeList, beforeList, contexts);
			}
			else {
				ArrayList<CopyGenerator> p = CopyGenerator.createGenerators(treeList, beforeList);
				assertTrue("Copy generator abstraction failed!", p.size() > 0);
				generator = p.get(0);
			}
			assertNotNull("creating of the generator failed!", generator);
			System.out.println(generator.toString());
			if (exp == null) {
				System.out.println("\n" + generator.toString());
				String tmpfname = "/tmp/" + onecase.getName() + ".po";
				System.out.println("Going to serialize to " + tmpfname);
				try {
					FileOutputStream fos = new FileOutputStream(tmpfname);
					ObjectOutputStream oos = new ObjectOutputStream(fos);
					oos.writeObject(generator);
					oos.close();
				}
				catch (IOException e) {
					e.printStackTrace();
					System.out.println("IOException during serialization!");
				}
			}
			else {
				VarGenerator expGen = null;
				try {
					FileInputStream fis = new FileInputStream(exp);
					ObjectInputStream ois = new ObjectInputStream(fis);
					expGen = (VarGenerator) ois.readObject();
					ois.close();
				}
				catch (Exception e) {
					e.printStackTrace();
					fail("Failed during deserialize from " + exp.getPath());
				}
				if (generator.generatorEquals(expGen)) {
					System.out.println("OK");
				}
				else {
					System.out.println("DIFF");
					System.out.println("Got:\n" + generator.toString());
					System.out.println("Exp:\n" + expGen.toString());
					continue;
				}
			}

			System.out.println("Generate back:");
			boolean pass = true;
			for (int i = 0; i < beforeList.size(); i++) {
				System.out.print("Snippet " + Integer.toString(i+1) + ":");
				ArrayList<MyCtNode> res = generator.generate(beforeList.get(i), facs.get(i), contexts.get(i));
				if (!expstr.containsKey(i+1)) {
					System.out.println();
					System.out.println("Target result:\n" + treeList.get(i).codeString());
					System.out.println("Total we get " + Integer.toString(res.size()));
					int cnt = 0;
					for (MyCtNode t : res) {
						cnt ++;
						System.out.println("Tree " + Integer.toString(cnt));
						String resStr = t.codeString();
						System.out.println(resStr);
					}
				}
				else {
					boolean found = false;
					for (MyCtNode t : res) {
						String resStr = t.codeString();
						if (resStr.trim().equals(expstr.get(i+1).trim()))
							found = true;
					}
					if (!found) {
						pass = false;
						System.out.println("NOT FOUND");
						System.out.println("Target result:\n" + expstr.get(i+1));
						System.out.println("Total we get " + Integer.toString(res.size()));
						int cnt = 0;
						for (MyCtNode t : res) {
							cnt ++;
							System.out.println("Tree " + Integer.toString(cnt));
							String resStr = t.codeString();
							System.out.println(resStr);
						}
					}
					else
						System.out.println("OK");
				}
			}
			if (pass)
				passedCnt ++;
		}
		assertTrue("Some cases failed!", cases.length == passedCnt);
	}

	@Test
	public void testEnumerationGenerator() {
		String[] cases = {"basic", "func", "varscope", "import", "import2", "langclass", "aslist", "instanceof"};
		//String[] cases = {"instanceof"};
		testGenerator("enum", cases, EnumerateGenerator.class);
	}

	@Test
	public void testCopyGenerator() {
		String[] cases = {"basic"};
		testGenerator("copy", cases, CopyGenerator.class);
	}
	
	@Test
	public void testReferenceGenerator() {
		String[] cases = {"bindref"};
		testGenerator("ref", cases, ReferenceGenerator.class);
	}
}

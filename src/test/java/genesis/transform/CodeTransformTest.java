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
package genesis.transform;

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
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.TreeMap;

import org.junit.Test;

import genesis.SnippetPairParser;
import genesis.node.MyCtNode;
import genesis.node.MyNodeSig;
import genesis.transform.CodeTransAbstractor;
import genesis.transform.CodeTransAdapter;
import genesis.transform.CodeTransform;
import junit.framework.TestCase;
import spoon.reflect.factory.Factory;

public class CodeTransformTest extends TestCase {

	@Test
	public void test() {
		URL folderURL = getClass().getResource("/transform/");
		assertNotNull("Test file not found!", folderURL);
		String[] cases =
			{"basic", "addguard", "addclause", "addparentheses", "addreturn", "binopchange", "changecond",
			 "addcase", "addelse", "removeblock", "removeguard", "changecall", "complicategen", "changecallbind",
			 "ifcontrol", "instanceof", "changecast", "changecastcall", "changecastfield", "changeclassaccess", 
			 "changecastfor", "trycatch", "instanceof2", "instanceof3", "instanceof4"};
		HashMap<String, Integer> caseTreeLimit = new HashMap<String, Integer>();
		caseTreeLimit.put("changecallbind", 70);
		String folder = folderURL.getPath();
		int totCnt = 0;
		int passedCnt = 0;
		System.out.println("AstGen Abstractor/Adapter unit test:");
		for (String casestr : cases) {
			File onecase = new File(folder + "/" + casestr);
			assertTrue("Unknown structure in resource /transform/", onecase.isDirectory());
			totCnt ++;
			File[] files = onecase.listFiles();
			TreeMap<Integer, File> befores = new TreeMap<Integer, File>();
			TreeMap<Integer, File> afters = new TreeMap<Integer, File>();
			TreeMap<Integer, String> expstr = new TreeMap<Integer, String>();
			File exp = null;
			CodeTransform expG = null;
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
					expstr.put(Integer.parseInt(fname.substring(6, idx)), l.get(0).replace(" ","").replace("\t","").trim());
					assertTrue("Wrong file name pattern " + fname, idx != -1);
				}
				else
					fail("Wrong file name pattern " + fname + " in " + casestr);
			}
			if (befores.size() != afters.size())
				fail("before/after pairs do not match!");

			CodeTransAbstractor ab = new CodeTransAbstractor();
			ArrayList<MyCtNode> roots1, roots2;
			ArrayList<Factory> factories;
			roots1 = new ArrayList<MyCtNode>();
			roots2 = new ArrayList<MyCtNode>();
			factories = new ArrayList<Factory>();
			for (Integer cid : befores.keySet()) {
				assertTrue("before/after pairs do not match!", afters.containsKey(cid));
				SnippetPairParser parser = new SnippetPairParser(befores.get(cid).getPath(), afters.get(cid).getPath());
				MyCtNode root1 = parser.getTree1();
				MyCtNode root2 = parser.getTree2();
				HashSet<MyNodeSig> inside = parser.getInsideSet();
				if ((root1 == null) || (root2 == null))
					fail("Cannot traverse down to the desired level: " + casestr);
				ab.addMapping(inside, root1, root2);
				roots1.add(root1);
				roots2.add(root2);
				factories.add(parser.getTree1Factory());
			}
			boolean genSucc = ab.generalize();
			assertTrue("AST generator generalization failed: " + casestr, genSucc);
			int numGen = ab.getNumGenerators();
			assertTrue("Num of AST generators is zero!", numGen > 0);
			System.out.print("Case " + onecase.getName() + ":\nAbstractor:");
			if (exp == null) {
				System.out.println(Integer.toString(befores.size()) + " snippets\n" + numGen + " result generators!");
				for (int i = 0; i < numGen; i++) {
					System.out.println("ASTGenerator " + i + ":");
					CodeTransform g = ab.getGenerator(i);
					System.out.println(g.toString());
					String tmpfname = "/tmp/" + onecase.getName() + i + ".po";
					System.out.println("Going to serialize to " + tmpfname);
					try {
						FileOutputStream fos = new FileOutputStream(tmpfname);
						ObjectOutputStream oos = new ObjectOutputStream(fos);
						oos.writeObject(g);
						oos.close();
					}
					catch (IOException e) {
						e.printStackTrace();
						System.out.println("IOException during serialization!");
					}
				}
				passedCnt ++;
				continue;
			}
			else {
				try {
					FileInputStream fis = new FileInputStream(exp);
					ObjectInputStream ois = new ObjectInputStream(fis);
					expG = (CodeTransform) ois.readObject();
					ois.close();
				}
				catch (Exception e) {
					e.printStackTrace();
					fail("Failed during deserialize from " + exp.getPath());
				}
				boolean found = false;
				for (int i = 0; i < numGen; i++) {
					CodeTransform g = ab.getGenerator(i);
					if (expG.generatorEquals(g)) {
						found = true;
						break;
					}
				}
				if (!found) {
					System.out.println("Not found the expected generator");
					System.out.println("expect:");
					System.out.println(expG.toString());
					for (int i = 0; i < numGen; i++) {
						CodeTransform g = ab.getGenerator(i);
						System.out.println("ASTGenerator " + i);
						System.out.println(g.toString());
					}
					continue;
				}
				else
					System.out.println("OK");
			}

			System.out.println("Adapter:");
			int n = roots1.size();
			boolean ok = true;
			for (int i = 0; i < n; i++) {
				System.out.print("Snippet " + Integer.toString(i+1) + ":");
				CodeTransAdapter aa = new CodeTransAdapter(expG, factories.get(i));
				boolean ret = aa.applyTo(roots1.get(i));
				assertTrue("Application of schema failed!", ret);
				if (!aa.covers(roots2.get(i))) {
					System.out.println("ASTGenerator does not cover the after tree!");
					ok = false;
				}
				else {
					long m = aa.prepareGenerate();
					boolean found = false;
					ArrayList<String> treestrs = new ArrayList<String>();
					for (int j = 0; j < m; j++) {
						MyCtNode genedTree = aa.generateOne();
						boolean passtcheck = aa.passTypecheck();
						if (genedTree != null && passtcheck) {
							String cstr = genedTree.codeString();
							treestrs.add(cstr);
							if (roots2.get(i).treeEquals(genedTree) ||
									roots2.get(i).codeString().equals(cstr) ||
									(expstr.containsKey(i+1) && expstr.get(i+1).equals(cstr.replace("\n", "").replace("\t","").replace(" ","").trim()))) {
								found = true;
								break;
							}
						}
					}
					boolean toomany = false;
					if (caseTreeLimit.containsKey(casestr)) {
						if (treestrs.size() > caseTreeLimit.get(casestr))
							toomany = true;
					}
					if (!found || toomany) {
						ok = false;
						if (!found)
							System.out.println("ASTGenerator does not find the after tree!");
						else
							System.out.println("ASTGenerator contains too many trees! Bound: " + caseTreeLimit.get(casestr));
						for (int j = 0; j < treestrs.size(); j++) {
							System.out.println("Tree " + (j + 1));
							System.out.println(treestrs.get(j));
						}
						System.out.println("Target: ");
						System.out.println(roots2.get(i).codeString());
					}
					else {
						System.out.println("OK, size " + treestrs.size() + " estimate size " + aa.estimateCost());
						/*for (int j = 0; j < treestrs.size(); j++) {
							System.out.println("Tree " + (j + 1));
							System.out.println(treestrs.get(j));
						}*/
					}
				}
			}
			if (ok) passedCnt ++;
		}
		if (totCnt != passedCnt)
			fail("Some cases produce unexpected output!");
	}

}

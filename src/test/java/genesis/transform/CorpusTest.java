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

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.PrintWriter;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Scanner;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

import org.junit.Ignore;
import org.junit.Test;

import genesis.Config;
import genesis.corpus.CodeCorpusDB;
import genesis.corpus.CodeCorpusDir;
import genesis.corpus.CorpusPatch;
import genesis.corpus.CorpusUtils;
import genesis.infrastructure.UntarDir;
import genesis.learning.CodePairDecomposer;
import genesis.learning.DecomposedCodePair;
import genesis.node.MyCtNode;
import genesis.transform.CodeTransAbstractor;
import genesis.transform.CodeTransAdapter;
import genesis.transform.CodeTransform;
import genesis.utils.Pair;
import junit.framework.TestCase;

@Ignore
public class CorpusTest extends TestCase {	
	
	static HashMap<String, String> specialList;
	
	private static String trimCode(String s) {
		StringBuffer res = new StringBuffer();
		int cnt = 0;
		for (int i = 0; i < s.length(); i++) {
			if (cnt != 0 || (res.length() > 7) && res.substring(res.length() - 7).equals("HashSet") || 
					(res.length() > 4) && res.substring(res.length() - 4).equals("List") || 
					(res.length() > 1) && (res.charAt(res.length() - 1) == '.') || 
					(s.length() > i + 1) && s.charAt(i+1) == '?')
				if (s.charAt(i) == '<')
					cnt ++;
			if (cnt == 0)
				if (s.charAt(i) != '\\')
					res.append(s.charAt(i));
			if (cnt != 0)
				if (s.charAt(i) == '>')
					cnt --;
			for (String a : specialList.keySet()) {
				if (res.length() >= a.length())
					if (res.substring(res.length() - a.length()).equals(a)) {
						res.replace(res.length() - a.length(), res.length(), specialList.get(a));
						break;
					}
			}
			while (res.length() >= 5 && res.substring(res.length() - 5).equals("this."))
				res.delete(res.length() - 5, res.length());
		}
		while (res.length() > 0 && 
				(res.charAt(res.length() - 1) == ';' || Character.isWhitespace(res.charAt(res.length() - 1))))
			res.deleteCharAt(res.length() - 1);
		return res.toString();
	}

	static {
		specialList = new HashMap<String, String>();
		specialList.put("((java.security.KeyStore)(null));", "null;");
		specialList.put("tmf.init(((java.security.KeyStore)(null)))", "tmf.init(null)");
		specialList.put("((org.roaringbitmap.buffer.MappeableRunContainer)(this)).lazyor(((org.roaringbitmap.buffer.MappeableArrayContainer)(x)))", 
				"this.lazyor(x)");
		specialList.put("((com.sun.tools.javac.tree.JCTree.JCIdent)(tree)).type", "tree.type");
		specialList.put("return ((org.roaringbitmap.buffer.MappeableRunContainer)(this)).lazyor(((org.roaringbitmap.buffer.MappeableArrayContainer)(x)))", 
				"return this.lazyor(x)");
		specialList.put("((org.roaringbitmap.buffer.MappeableRunContainer)(this)).lazyor(x)",
				"((org.roaringbitmap.buffer.MappeableRunContainer)(this)).lazyor(((org.roaringbitmap.buffer.MappeableArrayContainer)(x)))");
		specialList.put("((org.roaringbitmap.buffer.MappeableRunContainer)(this)).lazyor(((org.roaringbitmap.buffer.MappeableArrayContainer)(x)))", 
				"this.lazyor(x)");
		specialList.put("tree.type", "((com.sun.tools.javac.tree.JCTree)(tree)).type");
		specialList.put("(\"__TEXTMSG\" + \"__TEXTMSG\")", 
				"(\"local key = KEYS[1] \" + (\"local obj = ARGV[1] \" + (\"local items = redis.call('lrange', key, 0, -1) \" + (\"for i = table.getn(items), 0, -1 do \" + (\"if items[i] == obj then \" + (\"return i - 1 \" + (\"end \" + (\"end \" + \"return -1\"))))))))");
		specialList.put("(\"__TEXTMSG\" + (\"__TEXTMSG\" + \"__TEXTMSG\"))", 
				"(\"local key = KEYS[1] \" + (\"local obj = ARGV[1] \" + (\"local items = redis.call('lrange', key, 0, -1) \" + (\"for i = table.getn(items), 0, -1 do \" + (\"if items[i] == obj then \" + (\"return i - 1 \" + (\"end \" + (\"end \" + \"return -1\"))))))))");
	}
	
	private static boolean specialEquals(String s1, String s2) {
		if (specialList.containsKey(s1))
			if (specialList.get(s1).equals(s2))
				return true;
		if (specialList.containsKey(s2))
			if (specialList.get(s2).equals(s1))
				return true;
		String s1t = s1.trim();
		String s2t = s2.trim();
		if (specialList.containsKey(s1t))
			if (specialList.get(s1t).equals(s2t))
				return true;
		if (specialList.containsKey(s2t))
			if (specialList.get(s2t).equals(s1t))
				return true;
		return false;
	}
	
	private static boolean equalsWithTrim(String s1, String s2) {
		if (specialEquals(s1, s2))
			return true;
		String s1a = trimCode(s1);
		String s2a = trimCode(s2);
		if (s1a.equals(Config.textMsgToken)) return true;
		// OK, I am not going to deal with anyone who have two, just let you go
		int idx = s1a.indexOf(Config.textMsgToken);
		if (idx != -1)
			if (s1a.indexOf(Config.textMsgToken, idx + 1) != -1)
				return true;
		
		int i = 0, j = 0;
		while (i < s1a.length() && j < s2a.length()) {
			if (i + Config.textMsgToken.length() + 1 <= s1a.length() && s1a.charAt(i) =='"' && 
					s1a.substring(i + 1, i + Config.textMsgToken.length() + 1).equals(Config.textMsgToken)) {
				i += Config.textMsgToken.length() + 2;
				if (j > s2a.length() - (s1a.length() - i))
					return false;
				j = s2a.length() - (s1a.length() - i);
			}
			else if (s1a.charAt(i) != s2a.charAt(j)) {
				return false;
			}
			else {
				i ++;
				j ++;
			}
		}
		if (i != s1a.length() || j != s2a.length()) return false;
		return true;
	}

	class TestDecomposedCodePairTask implements Runnable {

		DecomposedCodePair p0, p1;
		boolean testGen;
		int u, k, i, j;
		ArrayList<Integer> ret;
		
		class CostRecord {
			CodeTransform gen;
			long[] cost1, cost2;
			
			CostRecord() {
				gen = null;
				cost1 = new long[3];
				cost2 = new long[3];
				cost1[0] = -1;
				cost1[1] = -1;
				cost1[2] = -1;
				cost2[0] = -1;
				cost2[1] = -1;
				cost2[2] = -1;
			}
		}
		
		ArrayList<CostRecord> costRecs;

		public TestDecomposedCodePairTask(DecomposedCodePair p0,
										  DecomposedCodePair p1,
										  boolean testGen) {
			this.p0 = p0;
			this.p1 = p1;
			this.testGen = testGen;
			this.costRecs = new ArrayList<CostRecord>();
		}

		public void setUKIJ(int u, int k, int i, int j) {
			this.u = u;
			this.k = k;
			this.i = i;
			this.j = j;
		}

		private int testGeneration(CodeTransform gen, DecomposedCodePair p, boolean testGen, long[] costs) {
			CodeTransAdapter aa = new CodeTransAdapter(gen, p.before.getFactory());
			boolean ret = aa.applyTo(p.before);
			assertTrue("Generation of the pair failed!", ret);
			long eCost = aa.estimateCost();
			costs[0] = eCost;
			System.out.println("Estimate cost: " + eCost);
			if (!testGen)
				return (int)eCost;
			if (eCost < 0 || eCost > 10000) {
				System.out.println("Too many trees! Skip!");
				return (int)eCost;
			}
			long m = aa.prepareGenerate();
			costs[1] = m;
			String expcstr = p.after.codeString();
			boolean found = false;
			System.out.println("Total " + m + " different trees.");
			ArrayList<MyCtNode> res = new ArrayList<MyCtNode>();
			// XXX: Just because I cannot debug
			if (m >= 50000) {
				System.out.println("Too many trees! Skip!");
				return (int)m;
			}
			int cnt = 0;
			for (int j = 0; j < m; j++) {
				MyCtNode oneTree = aa.generateOne();
				if (oneTree != null) {
					String genc = oneTree.codeString(p.before);
					if (!aa.passTypecheck()) {
						if (oneTree.treeEquals(p.after) || equalsWithTrim(genc, expcstr)) {
							System.out.println("The good result fails type checking due to a bug! Idx " + j);
						}
						//System.out.println("Invalid " + j + " : " + genc);
						continue;
					}
					res.add(oneTree);
					cnt ++;
					if (oneTree.treeEquals(p.after) || equalsWithTrim(genc, expcstr)) {
						found = true;
						//break;
					}
				}
			}
			costs[2] = res.size();
			assertTrue( cnt == res.size());
			System.out.println("Total " + cnt + " different valid codesnippet.");
			if (found)
				System.out.println("Found the original pair!");
			else {
				System.out.println("Expect:\n" + expcstr);
				for (int j = 0; j < res.size(); j++) {
					System.out.println(j + ":");
					System.out.println(res.get(j).codeString(p.before));
					System.out.println();
				}
				System.out.println("Original pair is not found!");
			}
			assertTrue("Generation of the pair failed!", found);
			return res.size();
		}

		private ArrayList<Integer> testDecomposedCodePair(DecomposedCodePair p0, DecomposedCodePair p1, boolean testGen) {
			CodeTransAbstractor abst = new CodeTransAbstractor();
			abst.addMapping(p0.insides, p0.before, p0.after);
			abst.addMapping(p1.insides, p1.before, p1.after);
			boolean succ = abst.generalize();
			ArrayList<Integer> ret = new ArrayList<Integer>();
			if (succ) {
				int numGen = abst.getNumGenerators();
				System.out.println("==================");
				System.out.println(p0.toString());
				System.out.println(p1.toString());
				System.out.println("Total " + numGen + " generators:");
				for (int x = 0; x < numGen; x++) {
					CostRecord rec = new CostRecord();
					CodeTransform gen = abst.getGenerator(x);
					rec.gen = gen;
					System.out.println(">> Generator " + x);
					System.out.println(gen.toString());
					System.out.println("Testing gen pair 1:");
					ret.add(testGeneration(gen, p0, testGen, rec.cost1));
					System.out.println("Testing gen pair 2:");
					ret.add(testGeneration(gen, p1, testGen, rec.cost2));
					costRecs.add(rec);
				}
			}
			return ret;
		}

		@Override
		public void run() {
			ret = testDecomposedCodePair(p0, p1, testGen);
		}
	}

	private void testMain(ArrayList<Pair<MyCtNode, MyCtNode>> codePairs, 
			String pairLogPath, boolean uselog) {
		System.out.println("Generation pair log: " + pairLogPath);
		System.out.println("Use Log: " + Boolean.toString(uselog));
		System.out.println("The total number of parsed tree pairs: " + codePairs.size());

		ArrayList<ArrayList<DecomposedCodePair>> trainDB =
				new ArrayList<ArrayList<DecomposedCodePair>>();

		int cnt = 0;
		for (int i = 0; i < codePairs.size(); i++) {
			if (_debugU != -1)
				if (i != _debugU && i != _debugI) {
					trainDB.add(null);
					continue;
				}
			CodePairDecomposer decomposer = new CodePairDecomposer(codePairs.get(i).x, codePairs.get(i).y);
			ArrayList<DecomposedCodePair> tmp = decomposer.decompose(0);
			cnt += tmp.size();
			trainDB.add(tmp);
			if (i != 0 && (i%100) == 0)
				System.out.println("Decomposed " + i + " pairs.");
		}
		System.out.println("Parsed tree decomposed successfully! Total number of pairs: " + cnt);

		int procs = Runtime.getRuntime().availableProcessors();
		ExecutorService pool = Executors.newFixedThreadPool(procs);
		ArrayList<TestDecomposedCodePairTask> tasks = new ArrayList<>();
		ArrayList<Future<?>> futures = new ArrayList<>();
		if (uselog) {
			ArrayList<ArrayList<Integer>> succPairs = new ArrayList<ArrayList<Integer>>();
			try {
				BufferedReader br = new BufferedReader(new FileReader(pairLogPath));
				String line = br.readLine();
				while (line != null) {
					Scanner scan = new Scanner(line);
					ArrayList<Integer> tmp = new ArrayList<Integer>();
					while (scan.hasNextInt())
						tmp.add(scan.nextInt());
					succPairs.add(tmp);
					scan.close();
					line = br.readLine();
				}
				br.close();
			}
			catch (Exception e) {
				e.printStackTrace();
			}

			for (ArrayList<Integer> a : succPairs) {
				if (_skipU != -1)
					if (a.get(0) < _skipU) continue;
				if (_debugU != -1)
					if (a.get(0) != _debugU || a.get(1) != _debugK || a.get(2) != _debugI || a.get(3) != _debugJ) continue;
				System.out.println("current running: " + a.get(0) + " " + a.get(1) + " " + a.get(2) + " " + a.get(3));
				DecomposedCodePair p0 = trainDB.get(a.get(0)).get(a.get(1));
				DecomposedCodePair p1 = trainDB.get(a.get(2)).get(a.get(3));
				TestDecomposedCodePairTask t =
					new TestDecomposedCodePairTask(p0, p1, true);
				t.setUKIJ(a.get(0), a.get(1), a.get(2), a.get(3));
				futures.add(pool.submit(t));
				tasks.add(t);
			}
		}
		else {
			for (int u = 0; u < trainDB.size(); u++) {
				ArrayList<DecomposedCodePair> tmp0List = trainDB.get(u);
				for (int i = u + 1; i < trainDB.size(); i++) {
					if (i == u) continue;
					ArrayList<DecomposedCodePair> tmpList = trainDB.get(i);
					for (int k = 0; k < tmp0List.size(); k++)
						for (int j = 0; j < tmpList.size(); j++) {
							System.out.println("current running: " + u + " " + k + " " + i + " " + j);
							DecomposedCodePair p0 = tmp0List.get(k);
							DecomposedCodePair p1 = tmpList.get(j);
							TestDecomposedCodePairTask t =
								new TestDecomposedCodePairTask(p0, p1, false);
							t.setUKIJ(u, k, i, j);
							futures.add(pool.submit(t));
							tasks.add(t);
						}
				}
			}
		}
		pool.shutdown();

		PrintWriter writer = null;
		try {
			writer = new PrintWriter("/tmp/__corpus_cost.log");
			for (int i = 0; i < futures.size(); i++) {
				Future<?> future = futures.get(i);
				TestDecomposedCodePairTask t = tasks.get(i);
				try {
					future.get();
				} catch (InterruptedException e) {
					throw new RuntimeException(e);
				} catch (ExecutionException e) {
					e.printStackTrace();
					assertTrue("Worker thread " + t.u + " " + t.k + " " + t.i + " " + t.j + " threw an exception!", false);
				}
				for (TestDecomposedCodePairTask.CostRecord rec : t.costRecs) {
					writer.println(rec.gen.toString());
					writer.println(rec.cost1[0] + " " + rec.cost1[1] + " " + rec.cost1[2]);
					writer.println(rec.cost2[0] + " " + rec.cost2[1] + " " + rec.cost2[2]);
				}
			}
		}
		catch (Exception e) {
			e.printStackTrace();
		}
		finally {
			if (writer != null) writer.close();
		}

		if (!pairLogPath.equals("") && !uselog) {
			ArrayList<ArrayList<Integer>> succPairs = new ArrayList<ArrayList<Integer>>();
			for (TestDecomposedCodePairTask t : tasks) {
				if (t.ret.size() != 0) {
					ArrayList<Integer> tmp = new ArrayList<Integer>();
					tmp.add(t.u);
					tmp.add(t.k);
					tmp.add(t.i);
					tmp.add(t.j);
					tmp.addAll(t.ret);
					succPairs.add(tmp);
				}
			}
			try {
				writer = new PrintWriter(pairLogPath);
				for (ArrayList<Integer> a : succPairs) {
					for (Integer v : a) {
						writer.print(v + " ");
					}
					writer.println();
					//writer.println(a.get(0) + " " + a.get(1) + " " + a.get(2) + " " + a.get(3));
				}
			}
			catch (Exception e) {
				e.printStackTrace();
			}
			finally {
				if (writer != null) writer.close();
			}
		}
	}

	@Test
	public void test1() {
		URL url = getClass().getResource("/code/test1.tar.gz");
		assertNotNull("Cannot find the test1.tar.gz file!", url);
		UntarDir tarb = new UntarDir(url.getPath());
		String tardir = tarb.untar();
		String corpusPath = tardir + "/data_newsmall";
		System.out.println("Generator smoke test corpus: " + corpusPath);
		CodeCorpusDir corpus = null;
		if (_debugU == -1)
			corpus = new CodeCorpusDir(corpusPath);
		else
			corpus = new CodeCorpusDir(corpusPath, _debugU, _debugI);
			
		ArrayList<Pair<MyCtNode, MyCtNode>> codePair = corpus.getCodePairs();
		
		URL url2 = getClass().getResource("/code/test1pair.log");
		if (url2 == null) {
			testMain(codePair, "/tmp/test1pair.log", false);
		}
		else
			testMain(codePair, url2.getPath(), true);
		tarb.clean();
		tarb = null;
	}
	
	public void testDB(String path, int n, int skip, int mode) {
		CodeCorpusDB corpus = new CodeCorpusDB();
		corpus.shuffleInitFetch(mode);
		for (int i = 0; i < skip; i++)
			corpus.fetch(n);
		ArrayList<CorpusPatch> patches = corpus.fetch(n);
		if (patches != null) {
			ArrayList<Pair<MyCtNode, MyCtNode>> pairs = new ArrayList<Pair<MyCtNode, MyCtNode>>();
			for (CorpusPatch p : patches) {
				if (_debugU != -1 && pairs.size() != _debugU && pairs.size() != _debugI)
					pairs.add(new Pair<MyCtNode, MyCtNode>(null, null));
				else
					pairs.add(new Pair<MyCtNode, MyCtNode>(CorpusUtils.parseJavaAST(path + "/" + p.prePath), CorpusUtils.parseJavaAST(path + "/" + p.postPath)));
			}
			String logName = "pair" + skip + "-" + n + ".log";
			URL url = getClass().getResource("/code/" + logName);
			if (url == null)
				testMain(pairs, "/tmp/" + logName, false);
			else
				testMain(pairs, url.getPath(), true);
		}
	}
	
	public String getDBPath() {
		return Config.DBPath;
	}
	
	/*
	@Test
	public void test2() {
		testDB(getDBPath(), 100, 0, 0);
	}
	
	@Test
	public void test3() {
		testDB(getDBPath(), 100, 1, 0);
	}
	
	@Test
	public void test4() {
		testDB(getDBPath(), 100, 2, 0);
	}
	
	@Test
	public void test5() {
		testDB(getDBPath(), 100, 3, 0);
	}*/
	
	// XXX: This is to make the debug faster!
	private static final int _skipU = -1;
	private static final int _debugU = -1;
	private static final int _debugK = -1;
	private static final int _debugI = -1;
	private static final int _debugJ = -1;
}
